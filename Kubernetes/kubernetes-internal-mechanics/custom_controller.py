from kubernetes import client, config, watch

def create_configmap(namespace, name, data):
    apps_v1_api = client.AppsV1Api()


    # Add health check probes to container
    container = client.V1Container(
        name=name,
        image=data.get('image', 'nginx'),
        ports=[client.V1ContainerPort(container_port=data.get('port', 80))],

        # Add these health checks
        liveness_probe=client.V1Probe(
            tcp_socket=client.V1TCPSocketAction(
                port=data.get('port', 80)
            ),
            initial_delay_seconds=30,
            period_seconds=10
        ),
        readiness_probe=client.V1Probe(
            tcp_socket=client.V1TCPSocketAction(
                port=data.get('port', 80)
            ),
            initial_delay_seconds=5,
            period_seconds=5
        )
    )

    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(namespace=namespace, name=f"{name}-deployment"),
        spec=client.V1DeploymentSpec(
            replicas=data.get('replicas', 1),
            selector=client.V1LabelSelector(match_labels={"app": name}),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": name}),
                spec=client.V1PodSpec(
                    containers=[container]
                )
            )
        )
    )

    try:
        apps_v1_api.create_namespaced_deployment(namespace=namespace, body=deployment)
        print(f"Deployment {name}-deployment created")
    except client.exceptions.ApiException as e:
        if e.status == 409:
            print(f"Deployment {name}-deployment already exists")
        else:
            print(f"Error creating deployment: {e}")

def delete_configmap(namespace, name):
    apps_v1_api = client.AppsV1Api()
    try:
        apps_v1_api.delete_namespaced_deployment(name=f"{name}-deployment", namespace=namespace)
        print(f"Deployment {name}-deployment deleted")
    except client.exceptions.ApiException as e:
        if e.status == 404:
            print(f"Deployment {name}-deployment not found")
        else:
            print(f"Error deleting deployment: {e}")


def reconcile_webapp(namespace, name, desired_spec):
    """Ensure the deployment matches the desired webapp spec."""
    apps_v1_api = client.AppsV1Api()
    try:
        # Check if deployment exists
        deployment = apps_v1_api.read_namespaced_deployment(name=f"{name}-deployment", namespace=namespace)

        # Compare current vs desired state
        current_replicas = deployment.spec.replicas
        desired_replicas = desired_spec.get('replicas', 1)

        if current_replicas != desired_replicas:
            print(f"Replica mismatch: current: {current_replicas}, desired: {desired_replicas}.")
            # Update deployment
            deployment.spec.replicas = desired_replicas
            apps_v1_api.patch_namespaced_deployment(name=f"{name}-deployment", namespace=namespace, body=deployment)
            print(f"Deployment {name}-deployment updated to {desired_replicas} replicas.")
        else:
            print(f"Deployment {name}-deployment is in sync.")

    except client.exceptions.ApiException as e:
        if e.status == 404:
            print(f"Deployment {name}-deployment not found, creating new deployment.")
            create_configmap(namespace, name, desired_spec)
        else:
            print(f"Error reconciling deployment: {e}")





def main():
    config.load_kube_config()
    api_instance = client.CustomObjectsApi()
    group = "example.com"
    version = "v1"
    namespace = "default"
    plural = "webapps"

    print("Controller started, watching for WebApp events...")
    
    resource_version = ""
    while True:
        stream = watch.Watch().stream(
            api_instance.list_namespaced_custom_object,
            group, version, namespace, plural,
            resource_version=resource_version
        )
        for event in stream:
            custom_resource = event['object']
            event_type = event['type']

            resource_name = custom_resource['metadata']['name']
            resource_data = custom_resource.get('spec', {})

            print(f"Event: {event_type} for WebApp: {resource_name}")

            if event_type == "ADDED":
                reconcile_webapp(namespace=namespace, name=resource_name, desired_spec=resource_data)
            elif event_type == "MODIFIED":
                reconcile_webapp(namespace=namespace, name=resource_name, desired_spec=resource_data)
            elif event_type == "DELETED":
                delete_configmap(namespace=namespace, name=resource_name)

            resource_version = custom_resource['metadata']['resourceVersion']

if __name__ == "__main__":
    main()