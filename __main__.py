"""A Google Cloud Python Pulumi program"""

from importlib.metadata import metadata
from typing import Mapping, Optional
from unicodedata import name
import pulumi
from pulumi_gcp import storage
from pulumi import Config, export, get_project, get_stack, Output, ResourceOptions
from pulumi_gcp.config import project, zone
from pulumi_gcp.container import Cluster, ClusterNodeConfigArgs

from pulumi_kubernetes import Provider
import pulumi_kubernetes
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import ContainerArgs, PodSpecArgs, PodTemplateSpecArgs, Service, ServicePortArgs, ServiceSpecArgs, Namespace, Secret, ConfigMap
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs
from pulumi_kubernetes.meta.v1.outputs import ObjectMeta
from pulumi_random import RandomPassword
from pulumi.resource import ResourceOptions
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts, FetchOpts
import pulumi_kubernetes as k8s

# Read in some configurable settings for our cluster:
config = Config(None)

# nodeCount is the number of cluster nodes to provision. Defaults to 3 if unspecified.
NODE_COUNT = config.get_int('node_count') or 3
# nodeMachineType is the machine type to use for cluster nodes. Defaults to n1-standard-1 if unspecified.
# See https://cloud.google.com/compute/docs/machine-types for more details on available machine types.
NODE_MACHINE_TYPE = config.get('node_machine_type') or 'n1-standard-1'
# username is the admin username for the cluster.
USERNAME = config.get('username') or 'admin'
# password is the password for the admin user in the cluster.
PASSWORD = config.get_secret('password') or RandomPassword("password", length=20, special=True).result
# master version of GKE engine
MASTER_VERSION = config.get('master_version')

SNYK_K8S_INTEGRATION_ID = config.get('snyk_K8s_integration_id') or 99999999999
SNYK_ORG_ID = config.get('snyk_org_id') or 99999999999

# Now, actually create the GKE cluster.
k8s_cluster = Cluster('pulumi-gke-cluster',
    initial_node_count=NODE_COUNT,
    node_version=MASTER_VERSION,
    min_master_version=MASTER_VERSION,
    node_config=ClusterNodeConfigArgs(
        machine_type=NODE_MACHINE_TYPE,
        oauth_scopes=[
            'https://www.googleapis.com/auth/compute',
            'https://www.googleapis.com/auth/devstorage.read_only',
            'https://www.googleapis.com/auth/logging.write',
            'https://www.googleapis.com/auth/monitoring'
        ],
    ),
)

# Manufacture a GKE-style Kubeconfig. Note that this is slightly "different" because of the way GKE requires
# gcloud to be in the picture for cluster authentication (rather than using the client cert/key directly).
k8s_info = Output.all(k8s_cluster.name, k8s_cluster.endpoint, k8s_cluster.master_auth)
k8s_config = k8s_info.apply(
    lambda info: """apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: {0}
    server: https://{1}
  name: {2}
contexts:
- context:
    cluster: {2}
    user: {2}
  name: {2}
current-context: {2}
kind: Config
preferences: {{}}
users:
- name: {2}
  user:
    auth-provider:
      config:
        cmd-args: config config-helper --format=json
        cmd-path: gcloud
        expiry-key: '{{.credential.token_expiry}}'
        token-key: '{{.credential.access_token}}'
      name: gcp
""".format(info[2]['cluster_ca_certificate'], info[1], '{0}_{1}_{2}'.format(project, zone, info[0])))

# Make a Kubernetes provider instance that uses our cluster from above.
k8s_provider = Provider('gke_k8s', kubeconfig=k8s_config)

# create snyk monitor namespace
monitor_namespace = Namespace(
  "snyk-monitor",
  metadata={
    "name": "snyk-monitor",
  },
  opts=ResourceOptions(provider=k8s_provider)
)

# create apples namespace this is where our applications will be deployed too
apples_namespace = Namespace(
  "apples",
  metadata={
    "name": "apples",
  },
  opts=ResourceOptions(provider=k8s_provider)
)

# Create Secret for the Snyk K8s Integration ID which we get from config
snyk_K8s_secret = Secret (
  "snyk-monitor",
  string_data={
    "integrationId": SNYK_K8S_INTEGRATION_ID,
    "dockercfg.json": '{}'
  },
  metadata={
    "name": "snyk-monitor",
    "namespace": "snyk-monitor"
  },
  opts=ResourceOptions(provider=k8s_provider)
)

# create Config Map for rego workload policy

snyk_monitor_custom_policies_str = """package snyk
orgs := ["%s"]
default workload_events = false
workload_events {
	input.metadata.namespace == "apples"
        input.kind != "CronJob"
        input.kind != "Service"
}""" % (SNYK_ORG_ID)

snyk_monitor_custom_policies_cm = ConfigMap(
  "snyk-monitor-custom-policies",
  metadata={
    "name": "snyk-monitor-custom-policies",
    "namespace": "snyk-monitor"
  },
  data={
    "workload-events.rego": snyk_monitor_custom_policies_str
  },
  opts=ResourceOptions(provider=k8s_provider)
)

# Deploy the snyk controller using it's helm chart
snyk_monitor_chart = Chart(
    "snyk-monitor",
    ChartOpts(
        chart="snyk-monitor",
        version="1.79.0",
        namespace="snyk-monitor",
        fetch_opts=FetchOpts(
            repo="https://snyk.github.io/kubernetes-monitor",
        ),
        values={
          "clusterName": "K8s-integration-demo-cluster",
          "policyOrgs": "{%s}" % (SNYK_ORG_ID),
          "workloadPoliciesMap": "snyk-monitor-custom-policies"
        }
    ),
    opts=ResourceOptions(provider=k8s_provider)
)

# deploy spring boot employee app

"""springboot employee api container, replicated 1 time."""
app_name = "springboot-employee-api"
app_labels = { "app": app_name }

springboot_employee_api = k8s.apps.v1.Deployment(
            app_name,
            metadata={
              "namespace": "apples",
            },
            spec=k8s.apps.v1.DeploymentSpecArgs(
                replicas=1,
                selector=k8s.meta.v1.LabelSelectorArgs(match_labels=app_labels),
                template=k8s.core.v1.PodTemplateSpecArgs(
                    metadata=k8s.meta.v1.ObjectMetaArgs(labels=app_labels),
                    spec=k8s.core.v1.PodSpecArgs(
                        containers=[
                            k8s.core.v1.ContainerArgs(
                                name=app_name,
                                image="pasapples/springbootemployee:cnb",
                                ports=[k8s.core.v1.ContainerPortArgs(
                                  container_port=8080
                                )]
                            )
                        ]
                    ),
                ),
            ),
            opts=ResourceOptions(provider=k8s_provider)
		)

"""Allocate an IP to the springboot employee api Deployment."""
frontend = k8s.core.v1.Service(
            app_name,
            metadata=k8s.meta.v1.ObjectMetaArgs(
                labels=app_labels,
                namespace="apples"),
            spec=k8s.core.v1.ServiceSpecArgs(
            	selector=app_labels,
                ports=[
                    k8s.core.v1.ServicePortArgs(
                        port=80,
                        target_port=8080,
                        protocol="TCP"
                    )
                ],
                type="LoadBalancer",
            ),
            opts=ResourceOptions(provider=k8s_provider)
        )

# Finally, export the kubeconfig so that the client can easily access the cluster.
export('kubeconfig', k8s_config)
