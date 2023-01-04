
import ipaddress
import string
import requests
import json
import google.auth
import google.auth.transport.requests
import time





project= 'sap-mce-devnetops-test2'
custstring= 'hec-ayg'
hostname='abc.com'
number='1'
sid='l1p'
port=44380
env='prod'
ip='10.238.106.5'
iparray=ip.split(',')


selfcert_file = open("cert.txt", "r")
 
#read whole file to a string
selfcert= selfcert_file.read()
 
#close file
selfcert_file.close()

privkey_file = open("key.txt", "r")
 
#read whole file to a string
privkey= privkey_file.read()
 
#close file
privkey_file.close()








credentials, project_id = google.auth.default(
        scopes=['https://www.googleapis.com/auth/cloud-platform'])


instancelist='https://compute.googleapis.com/compute/v1/projects/{}/aggregated/instances'.format(project)







instancegrpname='ig-'+custstring+'-http-ext-'+env+'-'+sid+'-'+number
sslpolicy_name='ssl-'+custstring+'-lb'
healthcheck_name='hc-'+custstring+'-ext-httplb-'+env+'-'+number
backendservice_name='bs-'+custstring+'-ext-httplb-'+env+'-'+number
targetproxy_name='lb-'+custstring+'-'+env+'-'+number
targetproxy_name2='lb2-'+custstring+'-'+env+'-'+number

urlmap_name='lb-'+custstring+'-'+env +'-'+number
fipname='fipvh'+custstring+'-'+ number
fwdurl_name='vh'+custstring+'-'+ number
cert_name= 'wildcert'+custstring
cloudarmor_name='ca-'+custstring
firewallrule_name='lbhealthcheck-'+custstring

gatewayname= 'cvg-'+custstring+'-'+number




request = google.auth.transport.requests.Request()
credentials.refresh(request)
token = credentials.token

headers = {'Authorization': 'Bearer ' + token}
















response = requests.get(instancelist, headers=headers)
print(response,'list')
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




addressurl='https://compute.googleapis.com/compute/beta/projects/{}/global/addresses'.format(project)

addressdata={

  "name": fipname

}

address_req=requests.post(addressurl,json=addressdata,headers=headers)
print(address_req,'fip')

certurl= 'https://compute.googleapis.com/compute/v1/projects/{}/global/sslCertificates'.format(project)
cert_data={
  "name": cert_name,
  "selfManaged": {
    "certificate": selfcert,
    "privateKey": privkey
  },
  "type": "SELF_MANAGED",
}

cert_req=requests.post(certurl,json=cert_data, headers=headers)
print(cert_req,'cert')

instancegrpurl= 'https://compute.googleapis.com/compute/v1/projects/{}/zones/{}/instanceGroups'.format(project,realzone)


instancegroupdata={
  
  "name": instancegrpname,
  "namedPorts": [
    {
      "name": 'https'+str(port),
      "port": port
    }
  ],
  "description": ""

}

instancegrp_req=requests.post(instancegrpurl,json=instancegroupdata, headers=headers)
print(instancegrp_req,'grp')

while 1:
  instancegrp_prov= requests.get(instancegrpurl+'/'+instancegrpname, headers=headers)
  if instancegrp_prov.status_code==200 :
      break

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
  print(instanceadd_req,'instance')
  time.sleep(5)

sslpolicy_url='https://compute.googleapis.com/compute/v1/projects/{}/global/sslPolicies'.format(project)
sslpolicy_data={
  "name": sslpolicy_name,
  "profile": "RESTRICTED",
  "minTlsVersion": "TLS_1_2",
  "description": "lb ssl policy"
}


sslpolicy_req=requests.post(sslpolicy_url,json=sslpolicy_data, headers=headers)
print(sslpolicy_req,'sslpolicy')


firewallrule_url='https://www.googleapis.com/compute/v1/projects/{}/global/firewalls'.format(project)

 
firewallrule_data={
  "kind": "compute#firewall",
  "name": firewallrule_name,
  
  "network": "projects/{}/global/networks{}".format(project,realnetwork),
  "direction": "INGRESS",
  "priority": 950,
  "allowed": [
    {
      "IPProtocol": "all"
    }
  ],
  "logConfig": {
    "enable": 'true'
  },
  "sourceRanges": [
    "35.191.0.0/16",
    "130.211.0.0/22"
  ]
}

firewallrule_req=requests.post(firewallrule_url,json=firewallrule_data, headers=headers)
print(firewallrule_req.text,'firewallrule')

cloudarmor_url='https://compute.googleapis.com/compute/v1/projects/{}/global/securityPolicies'.format(project)
cloudarmor_data={
  
  
  "kind": "compute#securityPolicy",
  "name": cloudarmor_name,
  "rules": [
    {
      "action": "deny(403)",
      "description": "CVE-2022-22963-Spring4Shell",
      "kind": "compute#securityPolicyRule",
      "match": {
        "expr": {
          "expression": "request.headers['class.module.classLoader.resources.context.parent.pipeline.first.pattern'].lower().matches('classloader')"
        }
      },
      "preview": 'false',
      "priority": 11000
    },
    {
      "action": "deny(403)",
      "description": "CVE-2022-22963-Spring4Shell",
      "kind": "compute#securityPolicyRule",
      "match": {
        "expr": {
          "expression": "request.headers['spring.cloud.function.routing-expression'].lower().matches('[.]exec[(]')"
        }
      },
      "preview": 'false',
      "priority": 11010
    },
    {
      "action": "deny(403)",
      "description": "CVE-2022-22963-Spring4Shell",
      "kind": "compute#securityPolicyRule",
      "match": {
        "expr": {
          "expression": "request.headers['class.module.classLoader.resources.context.parent.pipeline.first.pattern'].lower().matches('^(?:%{|<%)')"
        }
      },
      "preview": 'false',
      "priority": 11020
    },
    {
      "action": "deny(403)",
      "description": "CVE-2021-44228",
      "kind": "compute#securityPolicyRule",
      "match": {
        "expr": {
          "expression": "evaluatePreconfiguredExpr('cve-canary')"
        }
      },
      "preview": 'false',
      "priority": 11030
    },
    {
      "action": "allow",
      "description": "request.path.matches",
      "kind": "compute#securityPolicyRule",
      "match": {
        "expr": {
          "expression": "request.path.matches('/sap/[opu|es|bw|wdisp].*|/sap/bc/[webdynpro|ui5_ui5].*|/sap/bc/[srt/rfc/sap|srt/wsdl].*')\t"
        }
      },
      "preview": 'false',
      "priority": 12000
    },
    {
      "action": "deny(403)",
      "description": "URL block listing",
      "kind": "compute#securityPolicyRule",
      "match": {
        "expr": {
          "expression": "request.path.matches('/')"
        }
      },
      "preview": 'false',
      "priority": 12100
    },
    {
      "action": "deny(403)",
      "description": "",
      "kind": "compute#securityPolicyRule",
      "match": {
        "expr": {
          "expression": "evaluatePreconfiguredExpr('xss-stable', ['owasp-crs-v030001-id941190-xss', 'owasp-crs-v030001-id941310-xss', 'owasp-crs-v030001-id941150-xss', 'owasp-crs-v030001-id941320-xss', 'owasp-crs-v030001-id941330-xss', 'owasp-crs-v030001-id941340-xss'])\t"
        }
      },
      "preview": 'false',
      "priority": 1970
    },
    {
      "action": "deny(403)",
      "description": "Remote Code Execution(RCE)",
      "kind": "compute#securityPolicyRule",
      "match": {
        "expr": {
          "expression": "evaluatePreconfiguredExpr('rce-canary')\t"
        }
      },
      "preview": 'false',
      "priority": 1971
    },
    {
      "action": "deny(403)",
      "description": "Local File Inclusion (LFI),",
      "kind": "compute#securityPolicyRule",
      "match": {
        "expr": {
          "expression": "evaluatePreconfiguredExpr('lfi-canary')\t"
        }
      },
      "preview": 'false',
      "priority": 1972
    },
    {
      "action": "deny(403)",
      "description": "Remote File Inclusion (RFI)",
      "kind": "compute#securityPolicyRule",
      "match": {
        "expr": {
          "expression": "evaluatePreconfiguredExpr('rfi-canary')\t"
        }
      },
      "preview": 'false',
      "priority": 1973
    },
    {
      "action": "deny(403)",
      "description": "",
      "kind": "compute#securityPolicyRule",
      "match": {
        "expr": {
          "expression": "evaluatePreconfiguredExpr('sqli-stable', ['owasp-crs-v030001-id942110-sqli', 'owasp-crs-v030001-id942120-sqli', 'owasp-crs-v030001-id942150-sqli', 'owasp-crs-v030001-id942180-sqli', 'owasp-crs-v030001-id942200-sqli', 'owasp-crs-v030001-id942210-sqli', 'owasp-crs-v030001-id942260-sqli', 'owasp-crs-v030001-id942300-sqli', 'owasp-crs-v030001-id942310-sqli', 'owasp-crs-v030001-id942330-sqli', 'owasp-crs-v030001-id942340-sqli', 'owasp-crs-v030001-id942380-sqli', 'owasp-crs-v030001-id942390-sqli', 'owasp-crs-v030001-id942400-sqli', 'owasp-crs-v030001-id942410-sqli', 'owasp-crs-v030001-id942430-sqli', 'owasp-crs-v030001-id942440-sqli', 'owasp-crs-v030001-id942450-sqli', 'owasp-crs-v030001-id942251-sqli', 'owasp-crs-v030001-id942420-sqli', 'owasp-crs-v030001-id942431-sqli', 'owasp-crs-v030001-id942460-sqli', 'owasp-crs-v030001-id942421-sqli', 'owasp-crs-v030001-id942432-sqli'] )\t"
        }
      },
      "preview": 'false',
      "priority": 1980
    },
    {
      "action": "allow",
      "description": "default rule",
      "kind": "compute#securityPolicyRule",
      "match": {
        "config": {
          "srcIpRanges": [
            "*"
          ]
        },
        "versionedExpr": "SRC_IPS_V1"
      },
      "preview": 'false',
      "priority": 2147483647
    }
  ],
  
  "type": "CLOUD_ARMOR"
}


cloudarmor_req=requests.post(cloudarmor_url,json=cloudarmor_data, headers=headers)
print(cloudarmor_req,'CArmor')

healthcheck_url='https://compute.googleapis.com/compute/v1/projects/{}/global/healthChecks'.format(project)
healthcheck_data={
  "name": healthcheck_name,
  "checkIntervalSec": 5,
  "timeoutSec": 5,
  "healthyThreshold": 2,
  "unhealthyThreshold": 2,
  "tcpHealthCheck": {
    "port": port
  },
  "type": "TCP"
}

healthcheck_req=requests.post(healthcheck_url,json=healthcheck_data, headers=headers)
print(healthcheck_req,'hc')

while 1:
  hc_prov= requests.get(healthcheck_url+'/'+healthcheck_name, headers=headers)
  if hc_prov.status_code==200 :
      break

backendservice_url='https://compute.googleapis.com/compute/v1/projects/{}/global/backendServices'.format(project)
backendservice_data={
  "name": backendservice_name,
  "timeoutSec": 600,
  "portName": 'https'+str(port),
  "port": port,
  "protocol": "HTTPS",
  "backends": [
    {
      "balancingMode": "UTILIZATION",
      "group":instancegrpurl+'/'+instancegrpname ,
      "maxUtilization": 1
      
    }
  ],
  "healthChecks": [
    healthcheck_url+'/'+healthcheck_name
  ],
  "loadBalancingScheme": "EXTERNAL_MANAGED",
  "logConfig": {
    "enable": 'true',
    "sampleRate": 1
  },
  "securityPolicy": cloudarmor_url+'/'+cloudarmor_name,
  "connectionDraining": {
    "drainingTimeoutSec": 300
  },
  "sessionAffinity": "NONE",
  "localityLbPolicy": "ROUND_ROBIN"


  
}

backendservice_req=requests.post(backendservice_url,json=backendservice_data, headers=headers)
print(backendservice_req.status_code,'bs')

while 1:
  bs_prov= requests.get(backendservice_url+'/'+backendservice_name, headers=headers)
  time.sleep(20)
  if bs_prov.status_code==200 :
      break


urlmap_url='https://compute.googleapis.com/compute/beta/projects/{}/global/urlMaps'.format(project)
urlmap_data={
  "name": urlmap_name ,
  "defaultService": backendservice_url+'/'+backendservice_name
}

urlmap_req=requests.post(urlmap_url,json=urlmap_data,headers=headers)
print(urlmap_req,'lb')
while 1:
  lb_prov= requests.get(urlmap_url+'/'+urlmap_name, headers=headers)
  time.sleep(20)
  if lb_prov.status_code==200 :
      break

targetproxy_url= 'https://compute.googleapis.com/compute/v1/projects/{}/global/targetHttpsProxies'.format(project)

targetproxy_data={

  "sslCertificates": [
    "https://compute.googleapis.com/compute/v1/projects/{}/global/sslCertificates/{}".format(project,cert_name)
  ],
  "name": targetproxy_name,
  "sslPolicy": sslpolicy_url+'/'+sslpolicy_name ,
  "urlMap": urlmap_url+'/'+urlmap_name
  

}

targetproxy_req=requests.post(targetproxy_url,json=targetproxy_data, headers=headers)
print(targetproxy_req.status_code,'routingrule')
while 1:
  targetprx_prov= requests.get(targetproxy_url+'/'+targetproxy_name, headers=headers)
  time.sleep(20)
  if targetprx_prov.status_code==200 :
      break





forwardingrule_url='https://compute.googleapis.com/compute/beta/projects/{}/global/forwardingRules'.format(project)

forwardingrule_data={
  "IPAddress": addressurl+'/'+fipname,
  "portRange":"443-443" ,
  "loadBalancingScheme": "EXTERNAL_MANAGED",
  "name": fwdurl_name,
  "target": targetproxy_url+'/'+targetproxy_name
}

forwardingrule_req=requests.post(forwardingrule_url,json=forwardingrule_data,headers=headers)
print(forwardingrule_req,'frontend')
