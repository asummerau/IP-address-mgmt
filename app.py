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

filename = 'data.csv'
subnets = [
    {'subnet': '10.0.0.0/24', 'dhcp_range': ('10.0.0.151', '10.0.0.250')},
    {'subnet': '10.110.0.0/24', 'dhcp_range': ('10.110.0.11', '10.110.0.250')},
    {'subnet': '10.110.110.0/24', 'dhcp_range': ('10.110.110.11', '10.110.110.250')},
    {'subnet': '10.110.120.0/24', 'dhcp_range': ('10.110.120.11', '10.110.120.250')}
]

def is_dhcp_address(ip, subnet_info):
    dhcp_range = subnet_info['dhcp_range']
    if not dhcp_range:  # Handle empty DHCP ranges
        return False
    # Returns true if the specified ip lies within the reserved dhcp range
    return ipaddress.ip_address(dhcp_range[0]) <= ipaddress.ip_address(ip) <= ipaddress.ip_address(dhcp_range[1])


if os.path.exists(filename):
    df = pd.read_csv(filename)

else:
    
    ips = []
    for subnet_info in subnets:
        subnet = subnet_info['subnet']
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
    df = pd.DataFrame(ips)
    df.to_csv(filename, index=False)


@app.route('/', methods=['GET', 'POST'])
def index():
    df_json = df.to_json(orient='records')
    df_json = json.loads(df_json)
    return render_template('index.html', df=df_json, av_subnets=[s['subnet'] for s in subnets])


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

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="9000", debug=True)
