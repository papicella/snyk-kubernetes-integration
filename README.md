[![Deploy](https://get.pulumi.com/new/button.svg)](https://app.pulumi.com/new?template=https://github.com/papicella/snyk-kubernetes-integration/blob/main/README.md)

# Installing the Snyk Controller into a Google Kubernetes Engine (GKE) cluster with Pulumi

This example provisions a [Google Kubernetes Engine (GKE)](https://cloud.google.com/kubernetes-engine/) cluster, the Snyk controller for the Kubernetes Integration, confiugures auto-import of workloads from the `apples` namespace and then deploys a sample workload as a Deployment into the cluster, to test that the Snyk Kubernetes integration is working using infrastructure-as-code. This
demonstrates that you can manage both the Kubernetes objects themselves, in addition to underlying cloud infrastructure,
using a single configuration language (in this case, Python), tool, and workflow.

## Prerequisites

Ensure you have [Python 3](https://www.python.org/downloads/), a Pulumi account [Pulumi Account](https://www.pulumi.com/),  and [the Pulumi CLI](https://www.pulumi.com/docs/get-started/install/).

We will be deploying to Google Cloud Platform (GCP), so you will need an account. If you don't have an account,
[sign up for free here](https://cloud.google.com/free/). In either case,
[follow the instructions here](https://www.pulumi.com/docs/intro/cloud-providers/gcp/setup/) to connect Pulumi to your GCP account.

This example assumes that you have GCP's `gcloud` CLI on your path. This is installed as part of the
[GCP SDK](https://cloud.google.com/sdk/).

It’s important you use python 3 for this demo. To verify python 3 is in your path use a command as follows. Python 2 will not work for this demo. You may need to create an alias if you have python 2 installed along with python 3

```bash
❯ python --version
Python 3.9.9
```

## Snyk Pre Steps

Note: These must be done before running this example. We will need an existing Snyk ORG which does not have Kubernetes integration configured.

1. Select a Snyk ORG where you want to automatically setup the Kubernetes Integration for. It can be an empty Snyk ORG or even an existing one with projects but please ensure that the Kubernetes integration is not configured in this ORG

2. Click on `Integrations` then click on `Kubernetes` and finally click on `Connect`. Make a note of the `Integration ID` we will need it shortly

![alt tag](https://i.ibb.co/SPpzp5Q/pulumi-K8s-snyk-setup-1.png)

That's it you now ready to setup our Snyk Integration demo all from Pulumi using infrastructure-as-code, which will do the following

* Create a GKE cluster
* Deploy the Snyk Controller into the cluster
* Setup the Snyk Kubernetes Integration for auto import of K8s workloads into Snyk App
* Deploy a sample workload into the `apples` namespace as per our REGO policy file

## Running the Snyk Kubernetes Integration Setup 

After cloning this repo, `cd` into it and run these commands. 

1. Auth to Google Cloud using local authentication this is the easiest way to deploy this demo. There are other ways to configure pulumi with GCP but this is the easiest way for this demo
   
   ```bash
   $ gcloud auth login
   ```

2. Create a new stack, which is an isolated deployment target for this example. Please use `dev` as the example is setup to use the stack name `dev` :

    ```bash
    $ pulumi stack init dev
    ```

3. In many cases, different stacks for a single project will need differing values. For instance, you may want to use a different size for your GCP Compute Instance, or a different number of servers for your Kubernetes cluster between your development and production stacks.

    The key-value pairs for any given stack are stored in your project’s stack settings file, which is automatically named Pulumi.<stack-name>.yaml. You can typically ignore this file, although you may want to check it in and version it with your project source code.

    Add the following configuration variables to our stack as shown below:

    ```bash
    $ pulumi config set gcp:project [your-gcp-project-here] # Eg: snyk-cx-se-demo
    $ pulumi config set gcp:zone us-central1-c # any valid GCP zone here
    $ pulumi config set password --secret [your-cluster-password-here] # password for the cluster
    $ pulumi config set master_version 1.21.5-gke.1302 # any valid K8s master version on GKE
    ```

   By default, your cluster will have 3 nodes of type `n1-standard-1`. This is configurable, however; for instance
   if we'd like to choose 5 nodes of type `n1-standard-2` instead you can do that, run these commands to setup a 3 node cluster:

   ```bash
   $ pulumi config set node_count 3
   $ pulumi config set node_machine_type n1-standard-2
   ```

   Finally lets set the Snyk Kubernetes integration settings we will need to automatically setup the the Kubernetes integration into our cluster for us. We will need our Kubernetes Integration ID and our Snyk App ORG ID which will be the same ID's

   ```bash
   $ pulumi config set snyk_K8s_integration_id K8S_INTEGRATION_ID #same as ORG_ID at the moment
   $ pulumi config set snyk_org_id ORG_ID # your Snyk ORG ID under settings
   ```

   This shows how stacks can be configurable in useful ways. You can even change these after provisioning.

   Once this is done you should have a file `Pulumi.dev.yaml` with content as follows

   ```bash
   config:
    gcp-K8s-integration-demo:master_version: 1.21.5-gke.1302
    gcp-K8s-integration-demo:node_count: "3"
    gcp-K8s-integration-demo:node_machine_type: n1-standard-2
    gcp-K8s-integration-demo:password:
        secure: AAABAFeuJ0fR0k2SFMSVoJZI+0GlNYDaggXpRgu5sD0bpo+EnF1p4w==
    gcp-K8s-integration-demo:snyk_K8s_integration_id: yyyy1234
    gcp-K8s-integration-demo:snyk_org_id: yyyy1234
    gcp:project: snyk-cx-se-demo
    gcp:zone: us-central1-c
   ```

4. Deploy everything with the `pulumi up` command. This provisions all the GCP resources necessary for the Kubernetes Integration with Snyk, including
   your GKE cluster itself, Snyk Controller helm chart, and then deploys a Kubernetes Deployment running a Spring Boot application, all in a single step:

    ```bash
    $ pulumi up
    ```

   This will show you a preview, ask for confirmation, and then chug away at provisioning your Snyk K8s integration demo:

   ```bash
    ❯ pulumi up
    Previewing update (dev)

    View Live: https://app.pulumi.com/papicella/gcp-K8s-integration-demo/dev/previews/1db6492c-ae23-4e87-abf0-41e09fb62177

        Type                                                              Name                          Plan
    +   pulumi:pulumi:Stack                                               gcp-K8s-integration-demo-dev  create
    +   ├─ kubernetes:helm.sh/v3:Chart                                    snyk-monitor                  create
    +   │  ├─ kubernetes:core/v1:ServiceAccount                           snyk-monitor/snyk-monitor     create
    +   │  ├─ kubernetes:networking.k8s.io/v1:NetworkPolicy               snyk-monitor/snyk-monitor     create
    +   │  ├─ kubernetes:rbac.authorization.k8s.io/v1:ClusterRole         snyk-monitor                  create
    +   │  ├─ kubernetes:rbac.authorization.k8s.io/v1:ClusterRoleBinding  snyk-monitor                  create
    +   │  └─ kubernetes:apps/v1:Deployment                               snyk-monitor/snyk-monitor     create
    +   ├─ gcp:container:Cluster                                          pulumi-gke-cluster            create
    +   ├─ pulumi:providers:kubernetes                                    gke_k8s                       create
    +   ├─ kubernetes:core/v1:Namespace                                   snyk-monitor                  create
    +   ├─ kubernetes:core/v1:Namespace                                   apples                        create
    +   ├─ kubernetes:core/v1:ConfigMap                                   snyk-monitor-custom-policies  create
    +   ├─ kubernetes:core/v1:Service                                     springboot-employee-api       create
    +   ├─ kubernetes:core/v1:Secret                                      snyk-monitor                  create
    +   └─ kubernetes:apps/v1:Deployment                                  springboot-employee-api       create

    Resources:
        + 15 to create
   ```

   After about five minutes, your cluster will be ready, with the snyk controller installed, sample workload Deployment, auto imported into your Snyk ORG

   ```bash
   Do you want to perform this update? yes
    Updating (dev)

    View Live: https://app.pulumi.com/papicella/gcp-K8s-integration-demo/dev/updates/1

        Type                                                              Name                          Status
    +   pulumi:pulumi:Stack                                               gcp-K8s-integration-demo-dev  created
    +   ├─ kubernetes:helm.sh/v3:Chart                                    snyk-monitor                  created
    +   │  ├─ kubernetes:core/v1:ServiceAccount                           snyk-monitor/snyk-monitor     created
    +   │  ├─ kubernetes:networking.k8s.io/v1:NetworkPolicy               snyk-monitor/snyk-monitor     created
    +   │  ├─ kubernetes:rbac.authorization.k8s.io/v1:ClusterRole         snyk-monitor                  created
    +   │  ├─ kubernetes:rbac.authorization.k8s.io/v1:ClusterRoleBinding  snyk-monitor                  created
    +   │  └─ kubernetes:apps/v1:Deployment                               snyk-monitor/snyk-monitor     created
    +   ├─ gcp:container:Cluster                                          pulumi-gke-cluster            created
    +   ├─ pulumi:providers:kubernetes                                    gke_k8s                       created
    +   ├─ kubernetes:core/v1:Namespace                                   snyk-monitor                  created
    +   ├─ kubernetes:core/v1:Namespace                                   apples                        created
    +   ├─ kubernetes:core/v1:Service                                     springboot-employee-api       created
    +   ├─ kubernetes:core/v1:ConfigMap                                   snyk-monitor-custom-policies  created
    +   ├─ kubernetes:core/v1:Secret                                      snyk-monitor                  created
    +   └─ kubernetes:apps/v1:Deployment                                  springboot-employee-api       created

    Outputs:
        kubeconfig: "[secret]"

    Resources:
        + 15 created

    Duration: 6m28s
   ```

   The GKE cluster created on GCP

   ![alt tag](https://i.ibb.co/HtdYhrz/pulumi-K8s-snyk-setup-3.png)

   The Snyk Kubernetes Integration automatically configured

   ![alt tag](https://i.ibb.co/zRt7DRq/pulumi-K8s-snyk-setup-6.png)

   The sample workload auto imported from the `apples` namespace

    ![alt tag](https://i.ibb.co/m9Qq6Bb/pulumi-K8s-snyk-setup-4.png)
   
   ![alt tag](https://i.ibb.co/56FthSf/pulumi-K8s-snyk-setup-5.png)

   The Snyk Controller installed in the `snyk-monitor` namespace plus the config map and secret now managed by Pulumi 

   ```bash
   ❯ kubectl get all -n snyk-monitor
    NAME                              READY   STATUS    RESTARTS   AGE
    pod/snyk-monitor-db67744d-szl79   1/1     Running   0          8m52s

    NAME                           READY   UP-TO-DATE   AVAILABLE   AGE
    deployment.apps/snyk-monitor   1/1     1            1           8m53s

    NAME                                    DESIRED   CURRENT   READY   AGE
    replicaset.apps/snyk-monitor-db67744d   1         1         1       8m53s

    ❯ kubectl get secret -n snyk-monitor -l app.kubernetes.io/managed-by=pulumi
    NAME           TYPE     DATA   AGE
    snyk-monitor   Opaque   2      42m

    ❯ kubectl get configmap -n snyk-monitor -l app.kubernetes.io/managed-by=pulumi
    NAME                           DATA   AGE
    snyk-monitor-custom-policies   1      42m
   ```

   Let’s take a close look at the Python file __main__.py  and understand how the Snyk Kubernetes Integration was installed and configured for us. 

   REGO policy file used by the Snyk Controller which is currently hardcoded to only import workloads from the `apples` namespace. This can be changed in `__main__.py` and used as an external file rather then hard coded in the python code

   ```python
   snyk_monitor_custom_policies_str = """package snyk
    orgs := ["%s"]
    default workload_events = false
    workload_events {
        input.metadata.namespace == "apples"
            input.kind != "CronJob"
            input.kind != "Service"
    }""" % (SNYK_ORG_ID)
   ```

   Here is the Python code to install the Snyk Controller using it’s helm Chart. You will notice that we have specified the REPO to fetch the helm chart, provided the Snyk ORG ID as well as the custom policy file above. All of these are required to install the Snyk Controller into the GKE cluster and integrate it with Snyk.

   ```python
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
   ```

   The python code also deployed a Spring Boot sample application into our apples namespace which is what was auto imported by the Snyk Controller into Snyk App. The Python code to achieve that Deployment is as follows:

   ```python
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
   ```

5. From here, you may take this config and use it either in your `~/.kube/config` file, or just by saving it
   locally and plugging it into the `KUBECONFIG` envvar. All of your usual `gcloud` commands will work too, of course.

   For instance:

   ```bash
   $ pulumi stack output kubeconfig --show-secrets > kubeconfig.yaml
   $ KUBECONFIG=./kubeconfig.yaml kubectl get po -n apples
    NAME                                                READY   STATUS    RESTARTS   AGE
    springboot-employee-api-fyrj9hr2-66d8456f5f-hqqhx   1/1     Running   0          17m
   ```

6. At this point, you have a running cluster. Feel free to modify your program, and run `pulumi up` to redeploy changes.
   The Pulumi CLI automatically detects what has changed and makes the minimal edits necessary to accomplish these
   changes. This could be altering the existing chart, adding new GCP or Kubernetes resources, or anything, really.

7. Once you are done, you can destroy all of the resources, and the stack:

    ```bash
    $ pulumi destroy
    $ pulumi stack rm
    ```

    ```bash
    ❯ pulumi destroy
    Previewing destroy (dev)

    View Live: https://app.pulumi.com/papicella/gcp-K8s-integration-demo/dev/previews/44fb2e8b-641c-4f55-9b4b-4ffa78f340ee

        Type                                                              Name                          Plan
    -   pulumi:pulumi:Stack                                               gcp-K8s-integration-demo-dev  delete
    -   ├─ kubernetes:core/v1:Namespace                                   snyk-monitor                  delete
    -   ├─ kubernetes:core/v1:ConfigMap                                   snyk-monitor-custom-policies  delete
    -   ├─ kubernetes:core/v1:Secret                                      snyk-monitor                  delete
    -   ├─ kubernetes:core/v1:Namespace                                   apples                        delete
    -   ├─ kubernetes:core/v1:Service                                     springboot-employee-api       delete
    -   ├─ kubernetes:apps/v1:Deployment                                  springboot-employee-api       delete
    -   ├─ pulumi:providers:kubernetes                                    gke_k8s                       delete
    -   ├─ kubernetes:helm.sh/v3:Chart                                    snyk-monitor                  delete
    -   │  ├─ kubernetes:core/v1:ServiceAccount                           snyk-monitor/snyk-monitor     delete
    -   │  ├─ kubernetes:rbac.authorization.k8s.io/v1:ClusterRoleBinding  snyk-monitor                  delete
    -   │  ├─ kubernetes:networking.k8s.io/v1:NetworkPolicy               snyk-monitor/snyk-monitor     delete
    -   │  ├─ kubernetes:rbac.authorization.k8s.io/v1:ClusterRole         snyk-monitor                  delete
    -   │  └─ kubernetes:apps/v1:Deployment                               snyk-monitor/snyk-monitor     delete
    -   └─ gcp:container:Cluster                                          pulumi-gke-cluster            delete

    Outputs:
    - kubeconfig: "[secret]"

    Resources:
        - 15 to delete

    Do you want to perform this destroy? yes
    Destroying (dev)

    View Live: https://app.pulumi.com/papicella/gcp-K8s-integration-demo/dev/updates/2

        Type                                                              Name                          Status
    -   pulumi:pulumi:Stack                                               gcp-K8s-integration-demo-dev  deleted
    -   ├─ kubernetes:core/v1:Secret                                      snyk-monitor                  deleted
    -   ├─ kubernetes:core/v1:ConfigMap                                   snyk-monitor-custom-policies  deleted
    -   ├─ kubernetes:core/v1:Namespace                                   apples                        deleted
    -   ├─ kubernetes:core/v1:Namespace                                   snyk-monitor                  deleted
    -   ├─ kubernetes:core/v1:Service                                     springboot-employee-api       deleted
    -   ├─ kubernetes:apps/v1:Deployment                                  springboot-employee-api       deleted
    -   ├─ pulumi:providers:kubernetes                                    gke_k8s                       deleted
    -   ├─ kubernetes:helm.sh/v3:Chart                                    snyk-monitor                  deleted
    -   │  ├─ kubernetes:core/v1:ServiceAccount                           snyk-monitor/snyk-monitor     deleted
    -   │  ├─ kubernetes:networking.k8s.io/v1:NetworkPolicy               snyk-monitor/snyk-monitor     deleted
    -   │  ├─ kubernetes:rbac.authorization.k8s.io/v1:ClusterRoleBinding  snyk-monitor                  deleted
    -   │  ├─ kubernetes:rbac.authorization.k8s.io/v1:ClusterRole         snyk-monitor                  deleted
    -   │  └─ kubernetes:apps/v1:Deployment                               snyk-monitor/snyk-monitor     deleted
    -   └─ gcp:container:Cluster                                          pulumi-gke-cluster            deleted

    Outputs:
    - kubeconfig: "[secret]"

    Resources:
        - 15 deleted

    Duration: 3m40s

    The resources in the stack have been deleted, but the history and configuration associated with the stack are still maintained.
    If you want to remove the stack completely, run 'pulumi stack rm dev'.
    ```

<hr />

Pas Apicella [pas at snyk.io] is a Principal Solution Engineer APJ at Snyk