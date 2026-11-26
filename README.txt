# Wazuh Server - CPSC 491

This is the Wazuh server for our team's security monitoring project. It runs Ubuntu Server 24.04.3 LTS in VirtualBox with Wazuh 4.14.10.

VM setup: 8 GB RAM, 4 CPUs, 60 GB storage.

## Download and Setup

Google Drive: [https://drive.google.com/file/d/1iyWqKXxMk0kWYdeWQ3Fge9L0zx2HvkBv/view?usp=sharing]

1. Download the OVA file.
2. Open VirtualBox and select File > Import Appliance.
3. Select the OVA file and import it.
4. Start Ubuntu and log in with the test account provided privately.

## Wazuh

Wazuh collects and analyzes security events. Our team's backend will connect to Wazuh to retrieve security data, while the frontend will display the results.

To check that Wazuh is running:

`sudo systemctl is-active wazuh-manager wazuh-indexer wazuh-dashboard`

Agent monitoring and MCP scanner integration are planned next steps.

Only share a sanitized VM copy. 
