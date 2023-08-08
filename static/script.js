function loadIPAddresses() {
    var subnet = document.getElementById('subnet-select').value;
                
    if (subnet) {
        var tableHtml = '<h2>IP Addresses in Subnet: ' + subnet + '</h2>';
        tableHtml += '<table>';
        tableHtml += '<thead><tr><th>IP Address</th><th>Comment</th><th>In Use</th></tr></thead>';
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
                        tableHtml += '>';
                        tableHtml += '<td>' + row.ip_address + '</td>';
                        if (i === 0 || i === df.length - 1) {
                            tableHtml += '<td><input type="text" id="comment_' + i + '" value="' + (row.comment ? row.comment : '') + '" readonly></td>';
                            tableHtml += '<td><input type="checkbox" id="in_use_' + i + '" ' + (row.in_use ? 'checked' : '') + ' readonly></td>';
                        } else {
                            tableHtml += '<td><input type="text" id="comment_' + i + '" value="' + (row.comment ? row.comment : '') + '"></td>';
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
