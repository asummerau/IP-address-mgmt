function loadIPAddresses() {
    var subnet = document.getElementById('subnet-select').value;
                
    if (subnet) {
        var tableHtml = '<h2>IP Addresses in Subnet: ' + subnet + '</h2>';
        tableHtml += '<table>';
        tableHtml += '<thead><tr><th>IP Address</th><th class="middle-header">Comment</th><th>In Use</th></tr></thead>';
        tableHtml += '<tbody>';

        // Remove the following line:
        // var df = {{ df | tojson }};

        // Retrieve the data from the backend using AJAX, fetch, or any other method
        // Replace the URL below with the endpoint URL to fetch the data
        var url = '/getIPAddresses?subnet=' + subnet;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                var df = data; // Assuming the response is in the format of your previous data

                for (var i = 0; i < df.length; i++) {
                    var row = df[i];
                    if (row.subnet == subnet) {
                        tableHtml += '<tr';
                        if (row.in_use) {
                            tableHtml += ' class="checked-row"';
                        }
                        if (row.comment === "DHCP address") {
                            tableHtml += ' class="dhcp-row"';
                        } 
                        tableHtml += '>';
                        tableHtml += '<td>' + row.ip_address + '</td>';
                        
                        // Check if this row is the first, last, or has "DHCP address" in the comment
                        if (i === 0 || i === df.length - 1)
                        {
                            tableHtml += '<td><input type="text" id="comment_' + i + '" value="' + (row.comment ? row.comment : '') + '" readonly></td>';
                            tableHtml += '<td><input type="checkbox" id="in_use_' + i + '" ' + (row.in_use ? 'checked' : '') + ' readonly></td>';
                        }
                        else if (row.comment === "DHCP address") {
                            tableHtml += '<td class="middle-cell"><input type="text" id="comment_' + i + '" value="' + (row.comment ? row.comment : '') + '" readonly></td>';
                            tableHtml += '<td><input type="checkbox" id="in_use_' + i + '" ' + (row.in_use ? 'checked' : '') + ' readonly"></td>';
                        }
                        else {
                            tableHtml += '<td class="middle-cell"><input type="text" id="comment_' + i + '" value="' + (row.comment ? row.comment : '') + '"></td>';
                            tableHtml += '<td><input type="checkbox" id="in_use_' + i + '" ' + (row.in_use ? 'checked' : '') + ' onchange="handleCheckboxChange(this, this.parentNode.parentNode)"></td>';
                        }
                        tableHtml += '</tr>';
                    }
                }

                tableHtml += '</tbody>';
                tableHtml += '</table>';

                document.getElementById('ip-addresses-table-container').innerHTML = tableHtml;
            })
            .catch(error => {
                console.error('Error:', error);
                // Handle the error condition
            });
        document.getElementById('save-button-container').style.display = 'block';

    } else {
        document.getElementById('ip-addresses-table-container').innerHTML = '';
        document.getElementById('save-button-container').style.display = 'none';

    }
}

function saveData() {
    var subnet = document.getElementById('subnet-select').value;

    if (subnet) {
        var df = []; // Empty array to store the updated data
        df.push({'selectected_subnet': subnet})
        var rows = document.querySelectorAll('#ip-addresses-table-container table tbody tr');

        rows.forEach(function (row) {
            var ipElement = row.querySelector('td:first-child');
            var commentElement = row.querySelector('td:nth-child(2) input[type="text"]');
            var inUseElement = row.querySelector('td:nth-child(3) input[type="checkbox"]');

            if (ipElement && commentElement && inUseElement) {
                var ip = ipElement.innerText;
                var comment = commentElement.value;
                var inUse = inUseElement.checked;

                df.push({ subnet: subnet, ip_address: ip, comment: comment, in_use: inUse });
            }
        });

        // Send the data to the backend (you can use AJAX, fetch, or any other method)
        var url = '/save';
        var xhr = new XMLHttpRequest();
        xhr.open('POST', url, true);
        xhr.setRequestHeader('Content-Type', 'application/json');
        xhr.send(JSON.stringify(df));
    } else {
        console.log('Please select a subnet.');
    }
}

function handleCheckboxChange(checkbox, row) {
    if (checkbox.checked) {
        row.classList.add('checked-row');
    } else {
        row.classList.remove('checked-row');
    }
}

function exportToExcel() {
    window.location.href = '/exportExcel';
}

// Subnet Modal Functions
function showAddSubnetModal() {
    document.getElementById('add-subnet-modal').style.display = 'block';
}

function hideAddSubnetModal() {
    document.getElementById('add-subnet-modal').style.display = 'none';
    // Clear form
    document.getElementById('add-subnet-form').reset();
}

// Close modal when clicking outside of it
window.onclick = function(event) {
    var modal = document.getElementById('add-subnet-modal');
    if (event.target == modal) {
        hideAddSubnetModal();
    }
}

function addSubnet() {
    var subnetName = document.getElementById('subnet-name').value.trim();
    var subnetIp = document.getElementById('subnet-ip').value.trim();
    var prefixLength = document.getElementById('prefix-length').value;
    var dhcpStart = document.getElementById('dhcp-start').value.trim();
    var dhcpEnd = document.getElementById('dhcp-end').value.trim();

    // Validate inputs
    if (!subnetName || !subnetIp || !prefixLength) {
        alert('Please fill in all required fields (Subnet Name, Subnet IP, and Prefix Length).');
        return;
    }

    // Validate IP address format
    if (!isValidIP(subnetIp)) {
        alert('Please enter a valid IP address.');
        return;
    }

    // Validate DHCP range if provided
    if ((dhcpStart && !dhcpEnd) || (!dhcpStart && dhcpEnd)) {
        alert('Please provide both DHCP start and end addresses, or leave both empty.');
        return;
    }

    if (dhcpStart && dhcpEnd) {
        if (!isValidIP(dhcpStart) || !isValidIP(dhcpEnd)) {
            alert('Please enter valid DHCP range IP addresses.');
            return;
        }
    }

    // Construct subnet string
    var subnetString = subnetIp + '/' + prefixLength;

    // Prepare data to send
    var subnetData = {
        name: subnetName,
        subnet: subnetString,
        dhcp_start: dhcpStart || null,
        dhcp_end: dhcpEnd || null
    };

    // Send to backend
    fetch('/addSubnet', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(subnetData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Add new option to select dropdown
            var select = document.getElementById('subnet-select');
            var option = document.createElement('option');
            option.value = subnetString;
            option.text = subnetName + ' (' + subnetString + ')';
            select.appendChild(option);

            // Hide modal and reset form
            hideAddSubnetModal();
            
            alert('Subnet added successfully!');
        } else {
            alert('Error adding subnet: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error adding subnet. Please try again.');
    });
}

function isValidIP(ip) {
    var regex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
    return regex.test(ip);
}