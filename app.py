from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
from netaddr import IPNetwork
import ipaddress
import json
import os.path

app = Flask(__name__, static_folder='static', template_folder='template')

# # Sample data
# data = {
#     'ip_address': ['10.0.0.1', '10.0.0.2', '10.0.0.3'],
#     'comment': ['', '', ''],
#     'in_use': [False, False, False]
# }

filename = 'data_backup/data.csv'
subnets_filename = 'subnets.json'

# Load subnets from JSON file
def load_subnets():
    if os.path.exists(subnets_filename):
        with open(subnets_filename, 'r') as f:
            subnets_data = json.load(f)
            # Convert to the expected format
            subnets = []
            for subnet_info in subnets_data:
                dhcp_range = subnet_info.get('dhcp_range')
                if dhcp_range and len(dhcp_range) == 2:
                    dhcp_range = tuple(dhcp_range)
                else:
                    dhcp_range = None
                subnets.append({
                    'name': subnet_info.get('name', subnet_info['subnet']),  # Use subnet as name if not provided
                    'subnet': subnet_info['subnet'],
                    'dhcp_range': dhcp_range
                })
            return subnets
    else:
        # Default subnets if file doesn't exist
        return [
            {'name': 'DC Network', 'subnet': '10.0.0.0/24', 'dhcp_range': ('10.0.0.151', '10.0.0.250')},
            {'name': 'Main Site Network', 'subnet': '10.110.0.0/24', 'dhcp_range': ('10.110.0.11', '10.110.0.250')},
            {'name': 'Site A Network', 'subnet': '10.110.110.0/24', 'dhcp_range': ('10.110.110.11', '10.110.110.250')},
            {'name': 'Site B Network', 'subnet': '10.110.120.0/24', 'dhcp_range': ('10.110.120.11', '10.110.120.250')}
        ]

def save_subnets(subnets):
    # Convert to JSON format
    subnets_data = []
    for subnet_info in subnets:
        dhcp_range = subnet_info.get('dhcp_range')
        if dhcp_range:
            dhcp_range = list(dhcp_range)
        subnets_data.append({
            'name': subnet_info['name'],
            'subnet': subnet_info['subnet'],
            'dhcp_range': dhcp_range
        })
    
    with open(subnets_filename, 'w') as f:
        json.dump(subnets_data, f, indent=4)

# Load subnets at startup
subnets = load_subnets()

def is_dhcp_address(ip, subnet_info):
    dhcp_range = subnet_info['dhcp_range']
    if not dhcp_range:  # Handle empty DHCP ranges
        return False
    # Returns true if the specified ip lies within the reserved dhcp range
    return ipaddress.ip_address(dhcp_range[0]) <= ipaddress.ip_address(ip) <= ipaddress.ip_address(dhcp_range[1])

def generate_subnet_ips(subnet_info):
    """Generate IP addresses for a given subnet"""
    subnet = subnet_info['subnet']
    ips = []
    for ip in IPNetwork(subnet):
        ip_address = str(ip)
        ip_data = {
            'ip_address': ip_address,
            'comment': 'DHCP address' if is_dhcp_address(ip_address, subnet_info) else '',
            'subnet': subnet,
            'in_use': '',
            'editable': not is_dhcp_address(ip_address, subnet_info)
        }
        ips.append(ip_data)
    return ips

def regenerate_dataframe():
    """Regenerate the DataFrame with all current subnets"""
    global df
    ips = []
    for subnet_info in subnets:
        ips.extend(generate_subnet_ips(subnet_info))
    
    new_df = pd.DataFrame(ips)
    
    # If we have existing data, preserve comments and in_use status
    if 'df' in globals() and not df.empty:
        # Create a lookup for existing data
        existing_data = df.set_index('ip_address')
        new_df = new_df.set_index('ip_address')
        
        # Update new_df with existing data where available
        for ip in new_df.index:
            if ip in existing_data.index:
                new_df.loc[ip, 'comment'] = existing_data.loc[ip, 'comment']
                new_df.loc[ip, 'in_use'] = existing_data.loc[ip, 'in_use']
        
        new_df = new_df.reset_index()
    
    df = new_df
    df.to_csv(filename, index=False)


if os.path.exists(filename):
    df = pd.read_csv(filename)
    # Check if we need to regenerate data (new subnets added)
    existing_subnets = set(df['subnet'].unique()) if not df.empty else set()
    current_subnets = set([s['subnet'] for s in subnets])
    if existing_subnets != current_subnets:
        regenerate_dataframe()
else:
    regenerate_dataframe()


@app.route('/', methods=['GET', 'POST'])
def index():
    df_json = df.to_json(orient='records')
    df_json = json.loads(df_json)
    return render_template('index.html', df=df_json, subnets=subnets)


@app.route('/getIPAddresses', methods=['GET'])
def get_ip_addresses():
    subnet = request.args.get('subnet')  # Get the value of the 'subnet' query parameter
    
    filtered_ips = df.loc[df['subnet'] == subnet]
    df_json = filtered_ips.to_json(orient='records')
    df_json = json.loads(df_json)
    
    return df_json


@app.route('/save', methods=['POST'])
def save():
    updated_data = request.get_json()
    if updated_data:
        updated_data = pd.DataFrame(updated_data)

        df.set_index('ip_address', inplace=True)
        updated_data.set_index('ip_address', inplace=True)

        # Replace the rows in df with the matching rows from updated_data
        df.update(updated_data)
        df.reset_index(inplace=True)
        df.to_csv(filename, index=False)

    return 'Data saved successfully.'


@app.route('/exportExcel', methods=['GET'])
def export_excel():
    excel_filename = 'ip_addresses.xlsx'
    df.to_excel(excel_filename, index=False)
    return send_file(excel_filename, as_attachment=True)

@app.route('/addSubnet', methods=['POST'])
def add_subnet():
    try:
        data = request.get_json()
        subnet_name = data.get('name', '').strip()
        subnet_cidr = data.get('subnet')
        dhcp_start = data.get('dhcp_start')
        dhcp_end = data.get('dhcp_end')
        
        # Validate required fields
        if not subnet_name:
            return jsonify({'success': False, 'message': 'Subnet name is required'})
        
        if not subnet_cidr:
            return jsonify({'success': False, 'message': 'Subnet CIDR is required'})
        
        # Validate subnet format
        try:
            network = IPNetwork(subnet_cidr)
        except Exception as e:
            return jsonify({'success': False, 'message': 'Invalid subnet format'})
        
        # Check if subnet already exists
        existing_subnets = [s['subnet'] for s in subnets]
        if subnet_cidr in existing_subnets:
            return jsonify({'success': False, 'message': 'Subnet already exists'})
        
        # Check if name already exists
        existing_names = [s['name'] for s in subnets]
        if subnet_name in existing_names:
            return jsonify({'success': False, 'message': 'Subnet name already exists'})
        
        # Validate DHCP range if provided
        dhcp_range = None
        if dhcp_start and dhcp_end:
            try:
                start_ip = ipaddress.ip_address(dhcp_start)
                end_ip = ipaddress.ip_address(dhcp_end)
                network_obj = ipaddress.ip_network(subnet_cidr, strict=False)
                
                # Check if DHCP range is within the subnet
                if start_ip not in network_obj or end_ip not in network_obj:
                    return jsonify({'success': False, 'message': 'DHCP range must be within the subnet'})
                
                if start_ip >= end_ip:
                    return jsonify({'success': False, 'message': 'DHCP start must be less than DHCP end'})
                
                dhcp_range = (dhcp_start, dhcp_end)
                
            except Exception as e:
                return jsonify({'success': False, 'message': 'Invalid DHCP range'})
        
        # Add new subnet
        new_subnet = {
            'name': subnet_name,
            'subnet': subnet_cidr,
            'dhcp_range': dhcp_range
        }
        subnets.append(new_subnet)
        
        # Save subnets to file
        save_subnets(subnets)
        
        # Regenerate DataFrame with new subnet
        regenerate_dataframe()
        
        return jsonify({'success': True, 'message': 'Subnet added successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="9000", debug=True)
