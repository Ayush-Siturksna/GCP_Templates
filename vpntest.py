
"""This template creates a VPN tunnel, gateway, and forwarding rules."""


def generate_config(context):
    """ Entry point for the deployment resources. """

    number='1'
    properties = context.properties
    # array1=context.properties['localTrafficSelector']
    project_id = properties.get('project', context.env['project'])

    network = context.properties.get('networkURL', generate_network_uri(
        project_id,
        context.properties.get('network','')
    ))
    target_vpn_gateway =   'cvg-'+context.properties['name']+number
    esp_rule = target_vpn_gateway + '-esp-rule'
    udp_500_rule = target_vpn_gateway  + '-udp-500-rule'
    udp_4500_rule = target_vpn_gateway + '-udp-4500-rule'
    vpn_tunnel =  'vpn-'+context.properties['name']+ number
    route_test=  'route-'+vpn_tunnel
    resources = []
    if 'ipAddress' in context.properties:
        ip_address = context.properties['ipAddress']
        static_ip = ''
    else:
        static_ip =  'pip-cvg-'+context.properties['name']+ number
        resources.append({
            # The reserved address resource.
            'name': static_ip,
            # https://cloud.google.com/compute/docs/reference/rest/v1/addresses
            'type': 'gcp-types/compute-v1:addresses',
            'properties': {
                'name': properties.get('name', static_ip),
                'project': project_id,
                'region': context.properties['region']
            }
        })
        ip_address = '$(ref.' + static_ip + '.address)'

    resources.extend([
        {
            # The target VPN gateway resource.
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
                    'name': '{}-esp'.format(target_vpn_gateway) if 'name' in properties else esp_rule,
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
                    'name': '{}-udp-4500'.format(target_vpn_gateway) if 'name' in properties else udp_4500_rule,
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
                    'name': '{}-udp-500'.format(target_vpn_gateway) if 'name' in properties else udp_500_rule,
                    'project': project_id,
                    'IPAddress': ip_address,
                    'IPProtocol': 'UDP',
                    'portRange': 500,
                    'region': context.properties['region'],
                    'target': '$(ref.' + target_vpn_gateway + '.selfLink)',
                }
        },

    ])
    router_url_tag = 'routerURL'
    router_name_tag = 'router'

    if router_name_tag in context.properties:
        router_url = context.properties.get(router_url_tag, generate_router_uri(
            context.env['project'],
            context.properties['region'],
            context.properties[router_name_tag]))
        # Create dynamic routing VPN
        resources.extend([
            {
                # The VPN tunnel resource.
                'name': vpn_tunnel,
                # https://cloud.google.com/compute/docs/reference/rest/v1/vpnTunnels
                'type': 'gcp-types/compute-v1:vpnTunnels',
                'properties':
                    {
                        'name': properties.get('name', vpn_tunnel),
                        'project': project_id,
                        'description':
                            'A vpn tunnel',
                        'ikeVersion':
                            2,
                        'peerIp':
                            context.properties['peerAddress'],
                        'region':
                            context.properties['region'],
                        'router': router_url,
                        'sharedSecret':
                            context.properties['sharedSecret'],
                        'targetVpnGateway':
                            '$(ref.' + target_vpn_gateway + '.selfLink)'
                    },
                'metadata': {
                    'dependsOn': [esp_rule,
                                udp_500_rule,
                                udp_4500_rule]
                }
            }
             
            
            ])
    else:
        # Create static routing VPN
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
                        '$(ref.' + target_vpn_gateway + '.selfLink)',
                    'localTrafficSelector':
                        context.properties['localTrafficSelector'],
                    # 'remoteTrafficSelector':
                    #     context.properties['remoteTrafficSelector'],

                },
                'metadata': {
                    'dependsOn': [esp_rule, udp_500_rule, udp_4500_rule]
                }
            }
            , 
            
             {      
                   'name': route_test,
                   
                   'type': 'gcp-types/compute-v1:routes',
                   'properties': {
                    'name': route_test,
                    'description':
                        'A route',
                    'destRange': '192.1681.0/24',
                    'network': network,
                    'nextHopVpnTunnel': '$(ref.' + vpn_tunnel + '.selfLink)',
                    'priority': 1000
                     

                } ,

                    
                   'metadata': {
                    'dependsOn': [vpn_tunnel]
                   }
               } 
            
            
            ]
        )


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
                    'name': 'targetVpnGateway',
                    'value': target_vpn_gateway
                },
                {
                    'name': 'staticIp',
                    'value': static_ip
                },
                {
                    'name': 'espRule',
                    'value': esp_rule
                },
                {
                    'name': 'udp500Rule',
                    'value': udp_500_rule
                },
                {
                    'name': 'udp4500Rule',
                    'value': udp_4500_rule
                },
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

def generate_router_uri(project_id, region, router_name):
    """Format the router name as a router URI."""
    return 'projects/{}/regions/{}/routers/{}'.format(
        project_id,
        region,
        router_name
    )