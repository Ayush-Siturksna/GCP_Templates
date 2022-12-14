from audioop import add
import ipaddress
import requests
import json
import google.auth
import google.auth.transport.requests
# from apiconfig3 import *



project= 'sap-mce-devnetops-test2'
region = 'asia-southeast1'
routepriority= 990
custstring= 'hecayg'
number='1'
vpcnetwork='vpc-hec99-sap'





credentials, project_id = google.auth.default(
        scopes=['https://www.googleapis.com/auth/cloud-platform'])

gatewayurl = 'https://compute.googleapis.com/compute/v1/projects/{}/regions/{}/targetVpnGateways'.format(project,region)
routeurl='https://compute.googleapis.com/compute/v1/projects/{}/global/routes'.format(project)
addressurl='https://compute.googleapis.com/compute/v1/projects/{}/regions/{}/addresses'.format(project,region)
forwardingruleurl='https://compute.googleapis.com/compute/v1/projects/{}/regions/{}/forwardingRules'.format(project,region)
networkurl='https://compute.googleapis.com/compute/v1/projects/{}/global/networks/{}'.format(project,vpcnetwork)




ipname='pip-cvg-'+custstring+'-'+ number
gatewayname= 'cvg-'+custstring+'-'+number




request = google.auth.transport.requests.Request()
credentials.refresh(request)
token = credentials.token

headers = {'Authorization': 'Bearer ' + token}







routedata={
  "destRange": "192.168.4.0/24",
  "name": "testroute3",
  "network": "projects/sap-mce-devnetops-test2/global/networks/vpc-hec99-sap",
  "nextHopVpnTunnel": "projects/"+project+"/regions/"+region+"/vpnTunnels/con-hec99-sap-01",
  "priority": routepriority
}


addressdata={

  "name": ipname


}

gatewaydata={

   "name": gatewayname,
  "network": networkurl


}

fwdruledata={


"IPAddress": addressurl+'/'+ipname,
  "name": "Esp",
  "target": gatewayurl+'/'+gatewayname,
  "IPProtocol": "ESP"

}



# response = requests.get(gatewayurl, headers=headers)
ipadd=requests.post(addressurl,json=addressdata, headers=headers)
gateway=requests.post(gatewayurl,json=gatewaydata, headers=headers)
# fwdrule=requests.post(forwardingruleurl,json=fwdruledata, headers=headers)


print(ipadd.text , gateway.text)
