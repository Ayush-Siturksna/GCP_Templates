
import ipaddress
import string
import requests
import json
import google.auth
import google.auth.transport.requests





project= 'sap-mce-devnetops-test2'
custstring= 'hecayg'
number='1'
port=44380
env='prod'
ip='10.238.106.2'
iparray=ip.split(',')
region = 'asia-southeast1'
routepriority= 990


vpcnetwork='vpc-hec99-sap'





credentials, project_id = google.auth.default(
        scopes=['https://www.googleapis.com/auth/cloud-platform'])

gatewayurl = 'https://compute.googleapis.com/compute/v1/projects/{}/regions/{}/targetVpnGateways'.format(project,region)
instancelist='https://compute.googleapis.com/compute/v1/projects/{}/aggregated/instances'.format(project)
routeurl='https://compute.googleapis.com/compute/v1/projects/{}/global/routes'.format(project)
addressurl='https://compute.googleapis.com/compute/v1/projects/{}/regions/{}/addresses'.format(project,region)
forwardingruleurl='https://compute.googleapis.com/compute/v1/projects/{}/regions/{}/forwardingRules'.format(project,region)
networkurl='https://compute.googleapis.com/compute/v1/projects/{}/global/networks/{}'.format(project,vpcnetwork)



instancegrpname='ig-'+custstring+'-'+env+'-'+number
sslpolicy_name='ssl-'+custstring+'-lb'
ipname='pip-cvg-'+custstring+'-'+ number
gatewayname= 'cvg-'+custstring+'-'+number




request = google.auth.transport.requests.Request()
credentials.refresh(request)
token = credentials.token

headers = {'Authorization': 'Bearer ' + token}










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



response = requests.get(instancelist, headers=headers)
# ipadd=requests.post(addressurl,json=addressdata, headers=headers)
# gateway=requests.post(gatewayurl,json=gatewaydata, headers=headers)
# fwdrule=requests.post(forwardingruleurl,json=fwdruledata, headers=headers)


# data=response.json()




def findinstance(findip: string,response:string) -> string:
  data=response.json()
  for key in data['items']:

      for key2 in data['items'][key] :
          if key2=='instances':
            for x in data['items'][key][key2] :
                
              #    data2=json.loads(x)
                for y in x['networkInterfaces'] :
                    if y['networkIP']==findip:
                        return x['name']+','+x['zone']+','+y['subnetwork']+','+y['network']
                    else: 
                        for key3 in y:
                            if key3=='aliasIpRanges' :
                                  for cidr in y[key3] :
                                      if cidr['ipCidrRange']==findip+'/32':
                                          return x['name']+','+x['zone']+','+y['subnetwork']+','+y['network']
  return 0


instances=[]
zones=[]
subnets=[]
network=[]

for ips in iparray:
     array=findinstance(ips,response).split(',')
     instances.append(array[0])
     zones.append(array[1])
     subnets.append(array[2])
     network.append(array[3])


zn=zones[0]
nt=network[0]


index=zn.rfind('/')
nt_index=nt.rfind('/')
realzone=zn[index+1:]
realnetwork=nt[nt_index:]

instancegrpurl= 'https://compute.googleapis.com/compute/v1/projects/{}/zones/{}/instanceGroups'.format(project,realzone)


instancegroupdata={
  
  "name": instancegrpname,
  "namedPorts": [
    {
      "name": 'htpps'+str(port),
      "port": port
    }
  ],
  "description": ""

}

instancegrp_req=requests.post(instancegrpurl,json=instancegroupdata, headers=headers)


print(instancegrp_req)

instanceadd_url='https://compute.googleapis.com/compute/v1/projects/{}/zones/{}/instanceGroups/{}/addInstances'.format(project,realzone,instancegrpname)

for idx,inst in enumerate(instances):
  instanceadd_data={
    
    "instances": [
      {
        "instance": 'https://compute.googleapis.com/compute/v1/projects/{}/zones/{}/instances/{}'.format(project,realzone,instances[idx])
      }
    ]

  }

  instanceadd_req=requests.post(instanceadd_url,json=instanceadd_data, headers=headers)
  print(instanceadd_req)

sslpolicy_url='https://compute.googleapis.com/compute/v1/projects/{}/global/sslPolicies'.format(project)
sslpolicy_data={
  "name": sslpolicy_name,
  "profile": "RESTRICTED",
  "minTlsVersion": "TLS_1_2",
  "description": "lb ssl policy"
}

sslpolicy_req=requests.post(sslpolicy_url,json=sslpolicy_data, headers=headers)
print(sslpolicy_req)



