import time
import os
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

# Request network configuration
def network_creation(compute_service, project_id, default_region, vpc_name):
    network_body = {
        "autoCreateSubnetworks": False,
        "description": "Testing vpc automation",
        "mtu": 1460,
        "name": vpc_name,
        "routingConfig": {
            "routingMode": "REGIONAL"
        },
        "region": default_region
    }
    print("Creating network configuration")
    network_request = compute_service.networks().insert(project=project_id, body=network_body).execute()
    print("Waiting for network configuration")
    # Waiting for configuration to complete
    time.sleep(20)
    print("Network configuration done")

# Request subnetwork configuration
def subnet_creation(compute_service, project_id, default_region, sub_net_name, vpc_name):
    subnet_body = {
        "description": "Testing subnet",
        "enableFlowLogs": False,
        "ipCidrRange": "10.0.0.0/24",
        "name": sub_net_name,
        "network": "projects/cse5333-lab-1/global/networks/%s" % (vpc_name),
        "privateIpGoogleAccess": False,
        "region": default_region,
    }
    print("Creating subnet")
    request_subnet = compute_service.subnetworks().insert(project=project_id, 
                                        region=default_region, body=subnet_body).execute()

# Request ssh firewall configuration
def ssh_firewall_config(compute_service, project_id, default_region):
    firewall_body_ssh = {
        "allowed": [{
            "IPProtocol": "tcp",
            "ports": ["22"]
        }],
        "description": "Allows TCP connections from any source\
                        to any instance on the network using port 22.",
        "direction": "INGRESS",
        "name": "test-vpc-allow-ssh",
        "network": "projects/cse5333-lab-1/global/networks/test-vpc",
        "priority": 65534,
        "selfLink": "projects/cse5333-lab-1/global/firewalls/test-vpc-allow-ssh",
        "sourceRanges": ["0.0.0.0/0"]
    }
    print("Creating firewall rule for ssh")
    request_firewall_ssh = compute_service.firewalls().insert(project=project_id, 
                                        body=firewall_body_ssh).execute()

# Request http firewall configuration
def http_firewall_config(compute_service, project_id, default_region):
    firewall_body_http = {
        "allowed": [{
            "IPProtocol": "tcp",
            "ports": ["80","443"]
        }],
        "description": "Allows connection from any source to any\
                         instance on the network using custom protocols.",
        "direction": "INGRESS",
        "name": "test-vpc-allow-custom",
        "network": "projects/cse5333-lab-1/global/networks/test-vpc",
        "priority": 65534,
        "selfLink": "projects/cse5333-lab-1/global/firewalls/test-vpc-allow-custom",
        "sourceRanges": ["0.0.0.0/0"]
    }
    print("Creating firewall rule for http & https")
    request_firewall_http = compute_service.firewalls().insert(project=project_id,
                                        body=firewall_body_http).execute()

# Read ssh public file
def read_ssh_pub(ssh_pub):
    with open(os.path.expanduser(ssh_pub), 'r') as f:
        lines = f.readlines()
    return lines[0]

# Create compute engine
def create_instance(compute_service, project_id, zone_name,
                    image_name, image_project_name, instance_type, 
                    sub_net_name, default_region, disk_type, google_username, ssh_pub_key):
    print("Create instance")
    image_reponse = compute_service.images().getFromFamily(
                                project = image_project_name,
                                family = image_name
                            ).execute()
    source_disk_image = image_reponse['selfLink']

    # configure compute engine
    machine_type = 'zones/%s/machineTypes/%s' % (zone_name, instance_type)
    config = {
        "name": "test-instance-1",
        "machineType": "projects/cse5333-lab-1/zones/%s/machineTypes/%s" % (zone_name, instance_type),
        "disk": [
            {
                "autoDelete": True,
                "boot": True,
                "initializeParams": {
                    "diskSizeGb": "10",
                    "diskType": "projects/cse5333-lab-1/zones/%s/diskTypes/%s" % (zone_name, disk_type),
                    "sourceImage": source_disk_image,
                    },
            }],
        "metadata": 
        {
            "items": [
                {
                    "key": "ssh-keys",
                    "value": "%s:%s" % (google_username, ssh_pub_key)
                }
        ]},
        "networkInterfaces": [
            {
                "accessConfigs": [
                    {
                        "name": "External NAT",
                        "networkTier": "STANDARD"
                    }
                ],
                "stackType": "IPV4_ONLY",
                "subnetwork": "projects/cse5333-lab-1/regions/%s/subnetworks/%s" % (default_region, sub_net_name)
            }],
            "serviceAccounts": [
                {
                    "email": "142793266154-compute@developer.gserviceaccount.com",
                    "scopes": [
                        "https://www.googleapis.com/auth/devstorage.read_only",
                        "https://www.googleapis.com/auth/logging.write",
                        "https://www.googleapis.com/auth/monitoring.write",
                        "https://www.googleapis.com/auth/servicecontrol",
                        "https://www.googleapis.com/auth/service.management.readonly",
                        "https://www.googleapis.com/auth/trace.append"
                    ]
                }],
    }
    compute_engine_instance_request = compute_service.instances().insert(project=project_id,
                              zone=zone_name,
                              body=config).execute()

    print('Instance Id: ' + compute_engine_instance_request['targetId'])

# main function
def main():
    # Required argument
    google_cred = GoogleCredentials.get_application_default()
    compute_service = discovery.build('compute', 'v1', credentials=google_cred)
    # change it for different project id
    project_id = 'cse5333-lab-1'
    default_region = 'us-central1'
    vpc_name = "test-vpc"
    zone_name = "us-central1-a"
    image_name = "debian-11"
    image_project_name = "debian-cloud"
    instance_type = "e2-micro"
    sub_net_name = "test-subnet"
    disk_type = "pd-balanced"
    # Change your google username
    # Example "rishabhthakur@gmail.com"
    google_username = "rishabhthakur312"
    ssh_pub = "~/.ssh/id_rsa.pub"

    # VPC function call
    print("vpc creation started")
    print("------------------------------")
    network_creation(compute_service, project_id, default_region, vpc_name)  
    subnet_creation(compute_service, project_id, default_region, sub_net_name, vpc_name)
    ssh_firewall_config(compute_service, project_id, default_region)
    http_firewall_config(compute_service, project_id, default_region)
    time.sleep(20)
    print("vpc is created")
    print("------------------------------")

    # public ssh file function call
    ssh_pub_key = read_ssh_pub(ssh_pub)

    # Compute engine function call
    create_instance(compute_service, project_id, zone_name,image_name, 
                        image_project_name, instance_type, sub_net_name,
                        default_region, disk_type,google_username, ssh_pub_key)

if __name__ == "__main__":
    main()