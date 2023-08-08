from flask import Flask, render_template, request, jsonify
import pandas as pd
from netaddr import IPNetwork
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
subnets = ['10.0.0.0/24', '10.10.100.0/24', '10.20.0.0/24']

if os.path.exists(filename):
    df = pd.read_csv(filename)

else:
    
    ips = []
    for subnet in subnets:
        for ip in IPNetwork(subnet):
            #ips.append('%s' % ip)
            ip_addresses = {}
            ip_addresses['comment']=''
            ip_addresses['subnet']=subnet
            ip_addresses['ip_address']='%s' % ip
            ip_addresses['in_use']=False
            ips.append(ip_addresses)
    df = pd.DataFrame(ips)
    df.to_csv(filename, index=False)


@app.route('/', methods=['GET', 'POST'])
def index():
    df_json = df.to_json(orient='records')
    df_json = json.loads(df_json)
    return render_template('index.html', df=df_json, av_subnets=subnets)


@app.route('/getIPAddresses', methods=['GET'])
def get_ip_addresses():
    subnet = request.args.get('subnet')  # Get the value of the 'subnet' query parameter
    #filtered_ips = [ip for ip in ip_addresses if ip['subnet'] == subnet]  # Filter IP addresses by subnet
    filtered_ips = df.loc[df['subnet'] == subnet]
    df_json = filtered_ips.to_json(orient='records')
    df_json = json.loads(df_json)
    
    return df_json


@app.route('/save', methods=['POST'])
def save():
    updated_data = request.get_json()
    subnet = updated_data[0]['selectected_subnet']
    
    if updated_data:
        updated_data = pd.DataFrame(updated_data[1:])

        df.set_index('ip_address', inplace=True)
        updated_data.set_index('ip_address', inplace=True)

        # Replace the rows in df with the matching rows from updated_data
        df.update(updated_data)

        # Reset the index back to its original column
        df.reset_index(inplace=True)
      
        df.to_csv(filename, index=False)
        
    return 'Data saved successfully.'
    


if __name__ == '__main__':
    app.run(host="0.0.0.0", port="9000", debug=True)
