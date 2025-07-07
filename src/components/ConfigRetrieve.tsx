
import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { 
  Download, 
  Terminal, 
  Copy, 
  Save, 
  AlertCircle,
  CheckCircle,
  Clock,
  Server,
  FileText
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface ConfigOutput {
  command: string;
  output: string;
  timestamp: string;
  device: string;
  method: string;
}

const ConfigRetrieve = () => {
  const { toast } = useToast();
  const [selectedDevice, setSelectedDevice] = useState('');
  const [selectedCommand, setSelectedCommand] = useState('');
  const [selectedMethod, setSelectedMethod] = useState('netmiko');
  const [customCommand, setCustomCommand] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [saveBackup, setSaveBackup] = useState(true);
  const [configOutput, setConfigOutput] = useState<ConfigOutput | null>(null);

  const devices = [
    { value: 'R15', label: 'R15 - Core Router', status: 'online' },
    { value: 'R16', label: 'R16 - Distribution', status: 'online' },
    { value: 'R17', label: 'R17 - Access Layer', status: 'warning' },
    { value: 'R18', label: 'R18 - Border Router', status: 'offline' },
    { value: 'R19', label: 'R19 - MPLS PE', status: 'online' },
    { value: 'R20', label: 'R20 - Backup Core', status: 'online' }
  ];

  const commonCommands = [
    { value: 'show ip interface brief', label: 'Show IP Interface Brief' },
    { value: 'show version', label: 'Show Version' },
    { value: 'show running-config', label: 'Show Running Config' },
    { value: 'show ip route', label: 'Show IP Route' },
    { value: 'show interface status', label: 'Show Interface Status' },
    { value: 'show vlan brief', label: 'Show VLAN Brief' },
    { value: 'show cdp neighbors', label: 'Show CDP Neighbors' },
    { value: 'show inventory', label: 'Show Inventory' },
    { value: 'custom', label: 'Custom Command' }
  ];

  const methods = [
    { value: 'netmiko', label: 'Netmiko', description: 'Fast and reliable' },
    { value: 'napalm', label: 'NAPALM', description: 'Structured output' },
    { value: 'nornir', label: 'Nornir', description: 'Multi-threading' }
  ];

  const handleRetrieveConfig = async () => {
    if (!selectedDevice || (!selectedCommand && !customCommand)) {
      toast({
        title: "Validation Error",
        description: "Please select a device and command",
        variant: "destructive"
      });
      return;
    }

    setIsLoading(true);
    
    try {
      // Simulate API call
      const command = selectedCommand === 'custom' ? customCommand : selectedCommand;
      
      // Mock response - in real app this would be an API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockOutput = generateMockOutput(command, selectedDevice);
      
      const result: ConfigOutput = {
        command,
        output: mockOutput,
        timestamp: new Date().toISOString(),
        device: selectedDevice,
        method: selectedMethod
      };
      
      setConfigOutput(result);
      
      toast({
        title: "Success",
        description: `Configuration retrieved from ${selectedDevice}`,
      });
      
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to retrieve configuration",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const generateMockOutput = (command: string, device: string): string => {
    switch (command) {
      case 'show ip interface brief':
        return `Interface                  IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0         192.168.1.1     YES NVRAM  up                    up      
GigabitEthernet0/1         192.168.2.1     YES NVRAM  up                    up      
GigabitEthernet0/2         unassigned      YES NVRAM  administratively down down    
Loopback0                  10.1.1.${device.slice(-1)}        YES NVRAM  up                    up`;

      case 'show version':
        return `Cisco IOS Software, C2900 Software (C2900-UNIVERSALK9-M), Version 15.1(4)M12a
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2016 by Cisco Systems, Inc.
Compiled Fri 28-Oct-16 19:18 by prod_rel_team

ROM: System Bootstrap, Version 15.0(1r)M15, RELEASE SOFTWARE (fc1)

${device} uptime is 15 days, 4 hours, 23 minutes
System returned to ROM by power-on
System image file is "flash0:c2900-universalk9-mz.SPA.151-4.M12a.bin"`;

      case 'show running-config':
        return `Building configuration...

Current configuration : 2847 bytes
!
! Last configuration change at 14:23:45 UTC Mon Jan 1 2024
!
version 15.1
service timestamps debug datetime msec
service timestamps log datetime msec
no service password-encryption
!
hostname ${device}
!
boot-start-marker
boot-end-marker
!
enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0
!
no aaa new-model
!
interface GigabitEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 duplex auto
 speed auto
!
interface GigabitEthernet0/1
 ip address 192.168.2.1 255.255.255.0
 duplex auto
 speed auto
!
ip forward-protocol nd
!
no ip http server
no ip http secure-server
!
control-plane
!
line con 0
line aux 0
line vty 0 4
 password cisco
 login
 transport input all
!
scheduler allocate 20000 1000
!
end`;

      default:
        return `Output for command: "${command}" on device ${device}
        
This is mock output. In a real implementation, this would show the actual
command output from the network device using the selected automation method
(${selectedMethod}).

The command was executed successfully and the output would be displayed here.`;
    }
  };

  const handleCopyOutput = () => {
    if (configOutput) {
      navigator.clipboard.writeText(configOutput.output);
      toast({
        title: "Copied",
        description: "Output copied to clipboard",
      });
    }
  };

  const handleSaveToFile = () => {
    if (configOutput) {
      const blob = new Blob([configOutput.output], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${configOutput.device}_${configOutput.command.replace(/\s+/g, '_')}_${new Date().toISOString().split('T')[0]}.txt`;
      a.click();
      URL.revokeObjectURL(url);
      
      toast({
        title: "Saved",
        description: "Configuration saved to file",
      });
    }
  };

  const getDeviceStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      case 'offline':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Server className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-slate-800">Configuration Retrieve</h2>
        <p className="text-slate-600 mt-1">Execute commands and retrieve configurations from network devices</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Configuration Form */}
        <Card className="bg-white/80 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Terminal className="w-5 h-5 text-blue-600" />
              <span>Command Execution</span>
            </CardTitle>
            <CardDescription>Select device and command to execute</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Device Selection */}
            <div className="space-y-2">
              <Label htmlFor="device">Target Device</Label>
              <Select value={selectedDevice} onValueChange={setSelectedDevice}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a device" />
                </SelectTrigger>
                <SelectContent>
                  {devices.map((device) => (
                    <SelectItem key={device.value} value={device.value}>
                      <div className="flex items-center space-x-2">
                        {getDeviceStatusIcon(device.status)}
                        <span>{device.label}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Command Selection */}
            <div className="space-y-2">
              <Label htmlFor="command">Command</Label>
              <Select value={selectedCommand} onValueChange={setSelectedCommand}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a command" />
                </SelectTrigger>
                <SelectContent>
                  {commonCommands.map((cmd) => (
                    <SelectItem key={cmd.value} value={cmd.value}>
                      {cmd.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Custom Command Input */}
            {selectedCommand === 'custom' && (
              <div className="space-y-2">
                <Label htmlFor="customCommand">Custom Command</Label>
                <Textarea
                  id="customCommand"
                  value={customCommand}
                  onChange={(e) => setCustomCommand(e.target.value)}
                  placeholder="Enter your custom command..."
                  rows={3}
                />
              </div>
            )}

            {/* Method Selection */}
            <div className="space-y-2">
              <Label htmlFor="method">Automation Method</Label>
              <Select value={selectedMethod} onValueChange={setSelectedMethod}>
                <SelectTrigger>
                  <SelectValue placeholder="Select method" />
                </SelectTrigger>
                <SelectContent>
                  {methods.map((method) => (
                    <SelectItem key={method.value} value={method.value}>
                      <div>
                        <div className="font-medium">{method.label}</div>
                        <div className="text-xs text-slate-500">{method.description}</div>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Options */}
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="saveBackup"
                  checked={saveBackup}
                  onChange={(e) => setSaveBackup(e.target.checked)}
                  className="rounded border-gray-300"
                />
                <Label htmlFor="saveBackup" className="text-sm">
                  Save output as backup
                </Label>
              </div>
            </div>

            {/* Execute Button */}
            <Button 
              onClick={handleRetrieveConfig}
              disabled={isLoading || !selectedDevice}
              className="w-full bg-gradient-to-r from-blue-600 to-indigo-600"
            >
              {isLoading ? (
                <>
                  <Clock className="w-4 h-4 mr-2 animate-spin" />
                  Executing...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  Retrieve Configuration
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {/* Output Display */}
        <Card className="bg-white/80 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FileText className="w-5 h-5 text-green-600" />
                <span>Command Output</span>
              </div>
              {configOutput && (
                <div className="flex space-x-2">
                  <Button size="sm" variant="outline" onClick={handleCopyOutput}>
                    <Copy className="w-4 h-4 mr-1" />
                    Copy
                  </Button>
                  <Button size="sm" variant="outline" onClick={handleSaveToFile}>
                    <Save className="w-4 h-4 mr-1" />
                    Save
                  </Button>
                </div>
              )}
            </CardTitle>
            <CardDescription>
              {configOutput ? 
                `${configOutput.device} - ${configOutput.command} (${configOutput.method})` : 
                'Output will appear here after command execution'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {configOutput ? (
              <div className="space-y-4">
                {/* Output Metadata */}
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline" className="bg-blue-50 text-blue-700">
                    <Server className="w-3 h-3 mr-1" />
                    {configOutput.device}
                  </Badge>
                  <Badge variant="outline" className="bg-green-50 text-green-700">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    {configOutput.method}
                  </Badge>
                  <Badge variant="outline" className="bg-purple-50 text-purple-700">
                    <Clock className="w-3 h-3 mr-1" />
                    {new Date(configOutput.timestamp).toLocaleString()}
                  </Badge>
                </div>

                {/* Command Output */}
                <div className="bg-slate-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-auto max-h-96">
                  <pre className="whitespace-pre-wrap">{configOutput.output}</pre>
                </div>
              </div>
            ) : (
              <div className="text-center text-slate-500 py-12">
                <Terminal className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No output yet. Execute a command to see results.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ConfigRetrieve;
