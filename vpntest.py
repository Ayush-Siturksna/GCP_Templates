
"""This template creates a VPN tunnel, gateway, and forwarding rules."""


def generate_config(context):
    """ Entry point for the deployment resources.G """

    number= context.properties['number1']
    properties = context.properties
    array1=context.properties['remoteTrafficSelector']
    project_id = properties.get('project', context.env['project'])

    network = context.properties.get('networkURL', generate_network_uri(
        project_id,
        context.properties.get('network','')
    ))

    gateway_Uri='https://compute.googleapis.com/compute/v1/projects/'+context.env['project']+'/regions/'+context.properties['region']+'/targetVpnGateways/'+context.properties['gatewayname']
    target_vpn_gateway =   'cvg-'+context.properties['custstring']+'-'+number
    target_vpn_gateway_uri=''
    esp_rule = target_vpn_gateway + '-esp-rule'
    udp_500_rule = target_vpn_gateway  + '-udp-500-rule'
    udp_4500_rule = target_vpn_gateway + '-udp-4500-rule'
    vpn_tunnel =  'vpn-'+context.properties['custstring']+'-'+number
    router = 'cr-'+ context.properties['custstring'] + '-'+number
    peer_external_gateway = 'pvg-'+context.properties['custstring'] + '-'+number
    if context.properties['type']=='route' :
      localTrafficSelector=['0.0.0.0/0']
      remoteTrafficSelector=['0.0.0.0/0']
    elif context.properties['type']=='policy' :
      localTrafficSelector=context.properties['localTrafficSelector']
      remoteTrafficSelector=context.properties['remoteTrafficSelector']
    resources = []
   


    

    if context.properties['type']=='HA':




        
        # Create dynamic routing VPN O

        resources.extend([
            {
                # HA VPN gateway resource. U
                'name': target_vpn_gateway,
                # https://cloud.google.com/compute/docs/reference/rest/v1/targetVpnGatewaysahusy
                'type': 'gcp-types/compute-v1:vpnGateways',
                'properties':
                    {
                        'name': target_vpn_gateway,
                        'project': project_id,
                        'network': network,
                        'region': context.properties['region'],
                    }
            } ,
            
             {
                # HA VPN external gateway resource.R
                'name': peer_external_gateway,
                # https://cloud.google.com/compute/docs/reference/rest/v1/targetVpnGatewaysahusy
                'type': 'gcp-types/compute-v1:externalVpnGateways',
                'properties':
                    {
                        'name': peer_external_gateway,
                        'project': project_id,
                        'interfaces':[ 
                                {
                                'id': 0,
                                'ipAddress': context.properties['peerAddress']
                                }
                        ]
                         ,
                        'redundancyType': 'SINGLE_IP_INTERNALLY_REDUNDANT',

                        
                    }
            }
            
            
            
            ]) 



        resources.extend([
            {
                #  HA VPN router resource.A
                'name': router,
                # https://cloud.google.com/compute/docs/reference/rest/v1/routersahusy
                'type': 'gcp-types/compute-v1:routers',
                'properties':
                    {
                        'name': router,
                        'project': project_id,
                        'network': network,
                        'region': context.properties['region'],
                        'bgp': {
                                'asn': context.properties['googleasn'],
                                'keepaliveInterval': 20,
                                'advertiseMode': 'DEFAULT'
                                
                            }
                            
                    }
            } ]) 
            
        resources.extend([
            {
                # HA VPN tunnel resource.Y
                'name': vpn_tunnel,
                # https://cloud.google.com/compute/docs/reference/rest/v1/vpnTunnelsahusy
                'type': 'gcp-types/compute-v1:vpnTunnels',
                'properties':
                    {
                        'name':vpn_tunnel,
                        'project': project_id,
                        'description':
                            'HA vpn tunnel',
                        'ikeVersion':
                            2,
                        'peer_external_gateway':
                            '$(ref.' + peer_external_gateway + '.selfLink)' ,
                        'peerExternalGatewayInterface': 0,
                        'region':
                            context.properties['region'],
                        'router': '$(ref.' + router + '.selfLink)',
                        'sharedSecret':
                            context.properties['sharedSecret'],
                        'vpnGateway':
                            '$(ref.' + target_vpn_gateway + '.selfLink)',
                        'vpnGatewayInterface': 0   
                    },
                'metadata': {
                    'dependsOn': [router,peer_external_gateway,target_vpn_gateway]
                }
            }
             
            
            ])
    else:
        # Create static routing VPN U

        

        if context.properties['FreshClassicSetup']==1:
                if 'ipAddress' in context.properties:
                    ip_address = context.properties['ipAddress']
                    static_ip = ''
                else:
                    static_ip =  'pip-cvg-'+context.properties['custstring']+'-'+ number
                    resources.append({
                        # The reserved address resource. S
                        'name': static_ip,
                        # https://cloud.google.com/compute/docs/reference/rest/v1/addressesahusy
                        'type': 'gcp-types/compute-v1:addresses',
                        'properties': {
                            'name': properties.get('custstring', static_ip),
                            'project': project_id,
                            'region': context.properties['region']
                        }
                    })
                    ip_address = '$(ref.' + static_ip + '.address)'
                resources.extend([
                    {
                        # The target VPN gateway resource. H
                        'name': target_vpn_gateway,
                        # https://cloud.google.com/compute/docs/reference/rest/v1/targetVpnGateways
                        'type': 'gcp-types/compute-v1:targetVpnGateways',
                        'properties':
                            {
                                'name': target_vpn_gateway,
                                'project': project_id,
                                'network': network,
                                'region': context.properties['region'],
                            }
                    },
                    {
                        # The forwarding rule resource for the ESP traffic.
                        'name': esp_rule,
                        # https://cloud.google.com/compute/docs/reference/rest/v1/forwardingRules
                        'type': 'gcp-types/compute-v1:forwardingRules',
                        'properties':
                            {
                                'name': '{}-rule-esp'.format(target_vpn_gateway),
                                'project': project_id,
                                'IPAddress': ip_address,
                                'IPProtocol': 'ESP',
                                'region': context.properties['region'],
                                'target': '$(ref.' + target_vpn_gateway + '.selfLink)',
                            }
                    },
                    {
                        # The forwarding rule resource for the UDP traffic on port 4500.
                        'name': udp_4500_rule,
                        # https://cloud.google.com/compute/docs/reference/rest/v1/forwardingRules
                        'type': 'gcp-types/compute-v1:forwardingRules',
                        'properties':
                            {
                                'name': '{}-rule-udp4500'.format(target_vpn_gateway) ,
                                'project': project_id,
                                'IPAddress': ip_address,
                                'IPProtocol': 'UDP',
                                'portRange': 4500,
                                'region': context.properties['region'],
                                'target': '$(ref.' + target_vpn_gateway + '.selfLink)',
                            }
                    },
                    {
                        # The forwarding rule resource for the UDP traffic on port 500
                        'name': udp_500_rule,
                        # https://cloud.google.com/compute/docs/reference/rest/v1/forwardingRules
                        'type': 'gcp-types/compute-v1:forwardingRules',
                        'properties':
                            {
                                'name': '{}-rule-udp500'.format(target_vpn_gateway) ,
                                'project': project_id,
                                'IPAddress': ip_address,
                                'IPProtocol': 'UDP',
                                'portRange': 500,
                                'region': context.properties['region'],
                                'target': '$(ref.' + target_vpn_gateway + '.selfLink)',
                            }
                    },

                ])

                target_vpn_gateway_uri='$(ref.' + target_vpn_gateway + '.selfLink)'
                array2=[esp_rule, udp_500_rule, udp_4500_rule]

        else :
            
            
            target_vpn_gateway_uri=gateway_Uri
            array2=[]
             
  

        resources.extend(
            [{
                # The VPN tunnel resource.
                'name': vpn_tunnel,
                'type': 'gcp-types/compute-v1:vpnTunnels',
                'properties': {
                    'name': vpn_tunnel,
                    'description':
                        'A vpn tunnel',
                    'ikeVersion':
                        2,
                    'peerIp':
                        context.properties['peerAddress'],
                    'region':
                        context.properties['region'],
                    'sharedSecret':
                        context.properties['sharedSecret'],
                    'targetVpnGateway':
                        target_vpn_gateway_uri,
                    'localTrafficSelector':
                        localTrafficSelector,
                    'remoteTrafficSelector':
                        remoteTrafficSelector,

                },

                'metadata': {
                        'dependsOn': array2
                    }
            }
            
           
            
            
            ]
            )
        length = len(context.properties['remoteTrafficSelector'])
        for i in range(length):  
            resources.extend([     {      
                    'name': 'route-'+vpn_tunnel + '-' + str(i) ,
                    
                    'type': 'gcp-types/compute-v1:routes',
                    'properties': {
                        'name': 'route-'+vpn_tunnel + '-' + str(i) ,
                        'description':
                            'A route',
                        'destRange': array1[i],
                        'network': network,
                        'nextHopVpnTunnel': '$(ref.' + vpn_tunnel + '.selfLink)',
                        'priority': 1000
                        

                    } ,

                        
                    'metadata': {
                        'dependsOn': [vpn_tunnel]
                    }
                } ])


        # resources.append(
        #     {  
        #             "destRange": array1[0],
        #             'type': 'gcp-types/compute-v1:route',
        #             "name": properties.get('name', vpn_tunnel)+'-route',
        #             "network": network,
        #             "nextHopVpnTunnel": '$(ref.' + vpn_tunnel + '.selfLink)',
        #             "priority": 1000
        #              ,
        #            'metadata': {
        #             'dependsOn': [vpn_tunnel]
        #            }
        #        } 
                
        #      ,
        # )



    return {
        'resources':
            resources,
        'outputs':
            [
               
                {
                    'name': 'vpnTunnel',
                    'value': vpn_tunnel
                },
                {
                    'name': 'vpnTunnelUri',
                    'value': '$(ref.'+vpn_tunnel+'.selfLink)'
                }
            ]
    }

def generate_network_uri(project_id, network):
    """Format the resource name as a resource URI."""
    return 'projects/{}/global/networks/{}'.format(project_id, network)

# def generate_gateway_uri(project_id, region, gateway_name):
#     """Format the router name as a router URI."""
#     return 'https://compute.googleapis.com/compute/v1/projects/{}/regions/{}/targetVpnGateways/{}'.format(
#         project_id,
#         region,
#         gateway_name
#     )