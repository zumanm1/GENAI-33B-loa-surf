
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { 
  Database, 
  Search, 
  Download, 
  Eye,
  Calendar,
  Filter,
  RefreshCw,
  Archive,
  FileText,
  Clock,
  Server,
  Trash2
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface ConfigBackup {
  id: string;
  device: string;
  command: string;
  timestamp: string;
  size: string;
  method: string;
  content: string;
  tags: string[];
}

const BackupManager = () => {
  const { toast } = useToast();
  const [backups, setBackups] = useState<ConfigBackup[]>([]);
  const [filteredBackups, setFilteredBackups] = useState<ConfigBackup[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDevice, setSelectedDevice] = useState('all');
  const [selectedCommand, setSelectedCommand] = useState('all');
  const [selectedBackup, setSelectedBackup] = useState<ConfigBackup | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Mock data
  useEffect(() => {
    const mockBackups: ConfigBackup[] = [
      {
        id: '1',
        device: 'R15',
        command: 'show running-config',
        timestamp: '2025-01-07T10:30:00Z',
        size: '12.4 KB',
        method: 'netmiko',
        content: `Building configuration...

Current configuration : 2847 bytes
!
! Last configuration change at 14:23:45 UTC Mon Jan 1 2024
!
version 15.1
service timestamps debug datetime msec
service timestamps log datetime msec
no service password-encryption
!
hostname R15
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
router ospf 1
 network 192.168.1.0 0.0.0.255 area 0
 network 192.168.2.0 0.0.0.255 area 0
!
line con 0
line vty 0 4
 password cisco
 login
!
end`,
        tags: ['running-config', 'full-backup']
      },
      {
        id: '2',
        device: 'R16',
        command: 'show ip interface brief',
        timestamp: '2025-01-07T09:45:00Z',
        size: '1.2 KB',
        method: 'napalm',
        content: `Interface                  IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0         192.168.3.1     YES NVRAM  up                    up      
GigabitEthernet0/1         192.168.4.1     YES NVRAM  up                    up      
GigabitEthernet0/2         unassigned      YES NVRAM  administratively down down    
Loopback0                  10.1.1.16       YES NVRAM  up                    up`,
        tags: ['interface-status', 'quick-check']
      },
      {
        id: '3',
        device: 'R15',
        command: 'show version',
        timestamp: '2025-01-07T08:20:00Z',
        size: '3.8 KB',
        method: 'netmiko',
        content: `Cisco IOS Software, C2900 Software (C2900-UNIVERSALK9-M), Version 15.1(4)M12a
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2016 by Cisco Systems, Inc.
Compiled Fri 28-Oct-16 19:18 by prod_rel_team

ROM: System Bootstrap, Version 15.0(1r)M15, RELEASE SOFTWARE (fc1)

R15 uptime is 15 days, 4 hours, 23 minutes
System returned to ROM by power-on
System image file is "flash0:c2900-universalk9-mz.SPA.151-4.M12a.bin"

cisco C2911 (revision 1.0) with 487424K/36864K bytes of memory.
Processor board ID FTX152400KS
2 Gigabit Ethernet interfaces
DRAM configuration is 64 bits wide with parity disabled.
255K bytes of non-volatile configuration memory.
249856K bytes of ATA System CompactFlash 0 (Read/Write)`,
        tags: ['version-info', 'hardware-details']
      },
      {
        id: '4',
        device: 'R19',
        command: 'show ip route',
        timestamp: '2025-01-07T07:15:00Z',
        size: '5.2 KB',
        method: 'nornir',
        content: `Codes: L - local, C - connected, S - static, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area 
       N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2
       E1 - OSPF external type 1, E2 - OSPF external type 2
       i - IS-IS, su - IS-IS summary, L1 - IS-IS level-1, L2 - IS-IS level-2
       ia - IS-IS inter area, * - candidate default, U - per-user static route
       o - ODR, P - periodic downloaded static route, H - NHRP, l - LISP
       + - replicated route, % - next hop override

Gateway of last resort is not set

      10.0.0.0/8 is variably subnetted, 2 subnets, 2 masks
C        10.1.1.0/24 is directly connected, Loopback0
L        10.1.1.19/32 is directly connected, Loopback0
      192.168.1.0/24 is variably subnetted, 2 subnets, 2 masks
C        192.168.1.0/24 is directly connected, GigabitEthernet0/0
L        192.168.1.19/32 is directly connected, GigabitEthernet0/0`,
        tags: ['routing-table', 'network-topology']
      },
      {
        id: '5',
        device: 'R20',
        command: 'show running-config',
        timestamp: '2025-01-06T16:30:00Z',
        size: '15.1 KB',
        method: 'netmiko',
        content: `Building configuration...

Current configuration : 3142 bytes
!
version 15.1
service timestamps debug datetime msec
service timestamps log datetime msec
no service password-encryption
!
hostname R20
!
boot-start-marker
boot-end-marker
!
enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0
!
no aaa new-model
!
interface GigabitEthernet0/0
 description WAN Interface
 ip address 203.0.113.1 255.255.255.252
 duplex auto
 speed auto
!
interface GigabitEthernet0/1
 description LAN Interface  
 ip address 192.168.10.1 255.255.255.0
 duplex auto
 speed auto
!
router ospf 1
 router-id 10.1.1.20
 network 192.168.10.0 0.0.0.255 area 0
 network 203.0.113.0 0.0.0.3 area 0
!
end`,
        tags: ['running-config', 'backup-router']
      }
    ];

    setBackups(mockBackups);
    setFilteredBackups(mockBackups);
  }, []);

  // Filter backups based on search criteria
  useEffect(() => {
    let filtered = backups;

    if (searchTerm) {
      filtered = filtered.filter(backup => 
        backup.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
        backup.device.toLowerCase().includes(searchTerm.toLowerCase()) ||
        backup.command.toLowerCase().includes(searchTerm.toLowerCase()) ||
        backup.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    if (selectedDevice !== 'all') {
      filtered = filtered.filter(backup => backup.device === selectedDevice);
    }

    if (selectedCommand !== 'all') {
      filtered = filtered.filter(backup => backup.command === selectedCommand);
    }

    setFilteredBackups(filtered);
  }, [searchTerm, selectedDevice, selectedCommand, backups]);

  const handleSearch = () => {
    console.log('Searching for:', searchTerm);
    // In real app, this would trigger API call
  };

  const handleRefresh = async () => {
    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      toast({
        title: "Success",
        description: "Backup list refreshed successfully",
      });
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to refresh backup list",
        variant: "destructive"
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownloadBackup = (backup: ConfigBackup) => {
    const blob = new Blob([backup.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${backup.device}_${backup.command.replace(/\s+/g, '_')}_${backup.timestamp.split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    
    toast({
      title: "Downloaded",
      description: `Backup for ${backup.device} saved to file`,
    });
  };

  const handleViewBackup = (backup: ConfigBackup) => {
    setSelectedBackup(backup);
  };

  const handleDeleteBackup = (backupId: string) => {
    setBackups(prev => prev.filter(b => b.id !== backupId));
    toast({
      title: "Deleted",
      description: "Backup removed successfully",
    });
  };

  const uniqueDevices = [...new Set(backups.map(b => b.device))];
  const uniqueCommands = [...new Set(backups.map(b => b.command))];

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getMethodBadge = (method: string) => {
    const colors = {
      netmiko: 'bg-blue-100 text-blue-800 border-blue-200',
      napalm: 'bg-green-100 text-green-800 border-green-200',
      nornir: 'bg-purple-100 text-purple-800 border-purple-200'
    };
    return colors[method as keyof typeof colors] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-slate-800">Backup Manager</h2>
        <p className="text-slate-600 mt-1">Search, view, and manage configuration backups</p>
      </div>

      {/* Search and Filters */}
      <Card className="bg-white/80 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Search className="w-5 h-5 text-blue-600" />
            <span>Search & Filter</span>
          </CardTitle>
          <CardDescription>Find configuration backups by content, device, or command</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="md:col-span-2 space-y-2">
              <Label htmlFor="search">Search in configurations</Label>
              <div className="flex space-x-2">
                <Input
                  id="search"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Search for commands, IP addresses, interfaces..."
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                />
                <Button onClick={handleSearch} variant="outline">
                  <Search className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="device-filter">Device</Label>
              <Select value={selectedDevice} onValueChange={setSelectedDevice}>
                <SelectTrigger>
                  <SelectValue placeholder="All devices" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Devices</SelectItem>
                  {uniqueDevices.map((device) => (
                    <SelectItem key={device} value={device}>{device}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="command-filter">Command</Label>
              <Select value={selectedCommand} onValueChange={setSelectedCommand}>
                <SelectTrigger>
                  <SelectValue placeholder="All commands" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Commands</SelectItem>
                  {uniqueCommands.map((command) => (
                    <SelectItem key={command} value={command}>{command}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex items-center justify-between mt-4">
            <div className="text-sm text-slate-600">
              Showing {filteredBackups.length} of {backups.length} backups
            </div>
            <Button onClick={handleRefresh} variant="outline" disabled={isLoading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Backup List */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-white/80 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Archive className="w-5 h-5 text-green-600" />
              <span>Configuration Backups</span>
            </CardTitle>
            <CardDescription>Browse and manage saved configurations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {filteredBackups.length > 0 ? (
                filteredBackups.map((backup) => (
                  <div key={backup.id} className="p-4 bg-slate-50 rounded-lg border hover:bg-slate-100 transition-colors">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <Server className="w-4 h-4 text-blue-500" />
                          <span className="font-semibold text-slate-800">{backup.device}</span>
                          <Badge variant="outline" className={getMethodBadge(backup.method)}>
                            {backup.method}
                          </Badge>
                        </div>
                        
                        <p className="text-sm text-slate-600 mb-1">{backup.command}</p>
                        
                        <div className="flex items-center space-x-4 text-xs text-slate-500">
                          <span className="flex items-center space-x-1">
                            <Clock className="w-3 h-3" />
                            <span>{formatTimestamp(backup.timestamp)}</span>
                          </span>
                          <span className="flex items-center space-x-1">
                            <FileText className="w-3 h-3" />
                            <span>{backup.size}</span>
                          </span>
                        </div>

                        <div className="flex flex-wrap gap-1 mt-2">
                          {backup.tags.map((tag) => (
                            <Badge key={tag} variant="secondary" className="text-xs">
                              {tag}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      <div className="flex flex-col space-y-1 ml-4">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleViewBackup(backup)}
                        >
                          <Eye className="w-3 h-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDownloadBackup(backup)}
                        >
                          <Download className="w-3 h-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDeleteBackup(backup.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-slate-500 py-8">
                  <Database className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>No backups found</p>
                  <p className="text-xs mt-1">Try adjusting your search criteria</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Backup Viewer */}
        <Card className="bg-white/80 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="w-5 h-5 text-purple-600" />
              <span>Configuration Viewer</span>
            </CardTitle>
            <CardDescription>
              {selectedBackup 
                ? `${selectedBackup.device} - ${selectedBackup.command}`
                : 'Select a backup to view its contents'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedBackup ? (
              <div className="space-y-4">
                {/* Backup metadata */}
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline" className="bg-blue-50 text-blue-700">
                    <Server className="w-3 h-3 mr-1" />
                    {selectedBackup.device}
                  </Badge>
                  <Badge variant="outline" className={getMethodBadge(selectedBackup.method)}>
                    {selectedBackup.method}
                  </Badge>
                  <Badge variant="outline" className="bg-gray-50 text-gray-700">
                    <Clock className="w-3 h-3 mr-1" />
                    {formatTimestamp(selectedBackup.timestamp)}
                  </Badge>
                </div>

                {/* Configuration content */}
                <div className="bg-slate-900 text-green-400 p-4 rounded-lg font-mono text-xs overflow-auto max-h-80">
                  <pre className="whitespace-pre-wrap">{selectedBackup.content}</pre>
                </div>

                {/* Actions */}
                <div className="flex space-x-2">
                  <Button size="sm" onClick={() => handleDownloadBackup(selectedBackup)}>
                    <Download className="w-4 h-4 mr-2" />
                    Download
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => navigator.clipboard.writeText(selectedBackup.content)}>
                    <FileText className="w-4 h-4 mr-2" />
                    Copy
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center text-slate-500 py-12">
                <Eye className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No backup selected</p>
                <p className="text-xs mt-1">Click on a backup to view its contents</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default BackupManager;
