
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { 
  Server, 
  Plus, 
  Edit, 
  Trash2,
  TestTube,
  CheckCircle,
  AlertCircle,
  Clock,
  Network,
  Settings,
  Activity,
  Wifi,
  HardDrive
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface Device {
  id: string;
  name: string;
  host: string;
  port: number;
  deviceType: string;
  status: 'online' | 'offline' | 'warning' | 'testing';
  lastSeen: string;
  uptime: string;
  configBackups: number;
  responseTime: number;
  description?: string;
}

interface ConnectionTest {
  deviceId: string;
  status: 'testing' | 'success' | 'failed';
  message: string;
  responseTime?: number;
}

const DeviceManager = () => {
  const { toast } = useToast();
  const [devices, setDevices] = useState<Device[]>([]);
  const [connectionTests, setConnectionTests] = useState<ConnectionTest[]>([]);
  const [isTestingAll, setIsTestingAll] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [isEditing, setIsEditing] = useState(false);

  // Initialize with mock data
  useEffect(() => {
    const mockDevices: Device[] = [
      {
        id: '1',
        name: 'R15',
        host: '172.16.39.102',
        port: 32783,
        deviceType: 'cisco_ios_telnet',
        status: 'online',
        lastSeen: '2 minutes ago',
        uptime: '15d 4h 23m',
        configBackups: 12,
        responseTime: 245,
        description: 'Core Router - Primary'
      },
      {
        id: '2',
        name: 'R16',
        host: '172.16.39.102',
        port: 32773,
        deviceType: 'cisco_ios_telnet',
        status: 'online',
        lastSeen: '1 minute ago',
        uptime: '15d 4h 18m',
        configBackups: 8,
        responseTime: 198,
        description: 'Distribution Router'
      },
      {
        id: '3',
        name: 'R17',
        host: '172.16.39.102',
        port: 32763,
        deviceType: 'cisco_ios_telnet',
        status: 'warning',
        lastSeen: '10 minutes ago',
        uptime: '12d 2h 15m',
        configBackups: 5,
        responseTime: 850,
        description: 'Access Layer Router'
      },
      {
        id: '4',
        name: 'R18',
        host: '172.16.39.102',
        port: 32753,
        deviceType: 'cisco_ios_telnet',
        status: 'offline',
        lastSeen: '2 hours ago',
        uptime: 'N/A',
        configBackups: 15,
        responseTime: 0,
        description: 'Border Router'
      },
      {
        id: '5',
        name: 'R19',
        host: '172.16.39.102',
        port: 32743,
        deviceType: 'cisco_ios_telnet',
        status: 'online',
        lastSeen: '30 seconds ago',
        uptime: '20d 1h 45m',
        configBackups: 22,
        responseTime: 156,
        description: 'MPLS PE Router'
      },
      {
        id: '6',
        name: 'R20',
        host: '172.16.39.102',
        port: 32733,
        deviceType: 'cisco_ios_telnet',
        status: 'online',
        lastSeen: '45 seconds ago',
        uptime: '18d 6h 30m',
        configBackups: 18,
        responseTime: 203,
        description: 'Backup Core Router'
      }
    ];

    setDevices(mockDevices);
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      case 'offline':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'testing':
        return <Clock className="w-4 h-4 text-blue-500 animate-spin" />;
      default:
        return <Server className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'online':
        return <Badge className="bg-green-100 text-green-800 border-green-200">Online</Badge>;
      case 'warning':
        return <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200">Warning</Badge>;
      case 'offline':
        return <Badge className="bg-red-100 text-red-800 border-red-200">Offline</Badge>;
      case 'testing':
        return <Badge className="bg-blue-100 text-blue-800 border-blue-200">Testing</Badge>;
      default:
        return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  const getResponseTimeColor = (responseTime: number) => {
    if (responseTime === 0) return 'text-gray-500';
    if (responseTime < 300) return 'text-green-600';
    if (responseTime < 600) return 'text-yellow-600';
    return 'text-red-600';
  };

  const handleTestDevice = async (device: Device) => {
    setConnectionTests(prev => [
      ...prev.filter(t => t.deviceId !== device.id),
      { deviceId: device.id, status: 'testing', message: 'Connecting...' }
    ]);

    setDevices(prev => prev.map(d => 
      d.id === device.id ? { ...d, status: 'testing' } : d
    ));

    try {
      // Simulate connection test
      await new Promise(resolve => setTimeout(resolve, 2000 + Math.random() * 2000));
      
      const isSuccess = Math.random() > 0.3; // 70% success rate
      const responseTime = isSuccess ? Math.floor(Math.random() * 500) + 100 : 0;
      
      setConnectionTests(prev => [
        ...prev.filter(t => t.deviceId !== device.id),
        {
          deviceId: device.id,
          status: isSuccess ? 'success' : 'failed',
          message: isSuccess ? 'Connection successful' : 'Connection failed - timeout',
          responseTime: isSuccess ? responseTime : undefined
        }
      ]);

      setDevices(prev => prev.map(d => 
        d.id === device.id ? { 
          ...d, 
          status: isSuccess ? 'online' : 'offline',
          responseTime: isSuccess ? responseTime : 0,
          lastSeen: isSuccess ? 'just now' : d.lastSeen
        } : d
      ));

      toast({
        title: isSuccess ? "Connection Success" : "Connection Failed",
        description: `${device.name}: ${isSuccess ? 'Device is reachable' : 'Unable to connect'}`,
        variant: isSuccess ? "default" : "destructive"
      });

    } catch (error) {
      setConnectionTests(prev => [
        ...prev.filter(t => t.deviceId !== device.id),
        { deviceId: device.id, status: 'failed', message: 'Test failed' }
      ]);

      setDevices(prev => prev.map(d => 
        d.id === device.id ? { ...d, status: 'offline' } : d
      ));
    }

    // Clear test result after 5 seconds
    setTimeout(() => {
      setConnectionTests(prev => prev.filter(t => t.deviceId !== device.id));
    }, 5000);
  };

  const handleTestAllDevices = async () => {
    setIsTestingAll(true);
    
    // Test devices sequentially with small delays
    for (const device of devices) {
      await handleTestDevice(device);
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    setIsTestingAll(false);
    
    const onlineCount = devices.filter(d => d.status === 'online').length;
    toast({
      title: "Connectivity Test Complete",
      description: `${onlineCount}/${devices.length} devices are reachable`,
    });
  };

  const handleEditDevice = (device: Device) => {
    setSelectedDevice(device);
    setIsEditing(true);
  };

  const handleDeleteDevice = (deviceId: string) => {
    setDevices(prev => prev.filter(d => d.id !== deviceId));
    toast({
      title: "Device Removed",
      description: "Device has been removed from inventory",
    });
  };

  const getConnectionTestStatus = (deviceId: string) => {
    return connectionTests.find(t => t.deviceId === deviceId);
  };

  // Calculate summary statistics
  const totalDevices = devices.length;
  const onlineDevices = devices.filter(d => d.status === 'online').length;
  const warningDevices = devices.filter(d => d.status === 'warning').length;
  const offlineDevices = devices.filter(d => d.status === 'offline').length;
  const avgResponseTime = devices.filter(d => d.responseTime > 0).reduce((sum, d) => sum + d.responseTime, 0) / Math.max(1, devices.filter(d => d.responseTime > 0).length);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-slate-800">Device Manager</h2>
          <p className="text-slate-600 mt-1">Manage network device inventory and connectivity</p>
        </div>
        <div className="flex space-x-3">
          <Button variant="outline">
            <Plus className="w-4 h-4 mr-2" />
            Add Device
          </Button>
          <Button 
            onClick={handleTestAllDevices}
            disabled={isTestingAll}
            className="bg-gradient-to-r from-blue-600 to-indigo-600"
          >
            <TestTube className="w-4 h-4 mr-2" />
            {isTestingAll ? 'Testing...' : 'Test All'}
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-700">Total Devices</CardTitle>
            <Server className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-800">{totalDevices}</div>
            <p className="text-xs text-blue-600 mt-1">Network inventory</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-700">Online</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-800">{onlineDevices}</div>
            <p className="text-xs text-green-600 mt-1">{Math.round((onlineDevices / totalDevices) * 100)}% available</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-yellow-50 to-amber-50 border-yellow-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-yellow-700">Warning</CardTitle>
            <AlertCircle className="h-4 w-4 text-yellow-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-yellow-800">{warningDevices}</div>
            <p className="text-xs text-yellow-600 mt-1">Need attention</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-violet-50 border-purple-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-purple-700">Avg Response</CardTitle>
            <Activity className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-800">{Math.round(avgResponseTime)}ms</div>
            <p className="text-xs text-purple-600 mt-1">Network latency</p>
          </CardContent>
        </Card>
      </div>

      {/* Device List */}
      <Card className="bg-white/80 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Network className="w-5 h-5 text-blue-600" />
            <span>Device Inventory</span>
          </CardTitle>
          <CardDescription>Manage and monitor all network devices</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {devices.map((device) => {
              const testStatus = getConnectionTestStatus(device.id);
              
              return (
                <div key={device.id} className="p-6 bg-slate-50 rounded-lg border hover:bg-slate-100 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Device Header */}
                      <div className="flex items-center space-x-3 mb-3">
                        {getStatusIcon(device.status)}
                        <h3 className="text-lg font-semibold text-slate-800">{device.name}</h3>
                        {getStatusBadge(device.status)}
                        <Badge variant="outline" className="bg-slate-100 text-slate-700">
                          {device.deviceType.replace('_', ' ').toUpperCase()}
                        </Badge>
                      </div>

                      {/* Device Info */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        <div>
                          <p className="text-slate-500">Host</p>
                          <p className="font-medium">{device.host}:{device.port}</p>
                        </div>
                        <div>
                          <p className="text-slate-500">Last Seen</p>
                          <p className="font-medium">{device.lastSeen}</p>
                        </div>
                        <div>
                          <p className="text-slate-500">Uptime</p>
                          <p className="font-medium">{device.uptime}</p>
                        </div>
                        <div>
                          <p className="text-slate-500">Response Time</p>
                          <p className={`font-medium ${getResponseTimeColor(device.responseTime)}`}>
                            {device.responseTime > 0 ? `${device.responseTime}ms` : 'N/A'}
                          </p>
                        </div>
                      </div>

                      {/* Device Description */}
                      {device.description && (
                        <p className="text-sm text-slate-600 mt-2">{device.description}</p>
                      )}

                      {/* Connection Test Status */}
                      {testStatus && (
                        <div className="mt-3 p-2 bg-white rounded border">
                          <div className="flex items-center space-x-2">
                            {testStatus.status === 'testing' && (
                              <Clock className="w-4 h-4 text-blue-500 animate-spin" />
                            )}
                            {testStatus.status === 'success' && (
                              <CheckCircle className="w-4 h-4 text-green-500" />
                            )}
                            {testStatus.status === 'failed' && (
                              <AlertCircle className="w-4 h-4 text-red-500" />
                            )}
                            <span className="text-sm font-medium">{testStatus.message}</span>
                            {testStatus.responseTime && (
                              <span className="text-xs text-slate-500">({testStatus.responseTime}ms)</span>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Device Stats */}
                      <div className="flex items-center space-x-6 mt-4 text-xs text-slate-500">
                        <span className="flex items-center space-x-1">
                          <HardDrive className="w-3 h-3" />
                          <span>{device.configBackups} backups</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <Wifi className="w-3 h-3" />
                          <span>Telnet</span>
                        </span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex flex-col space-y-2 ml-6">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleTestDevice(device)}
                        disabled={device.status === 'testing'}
                      >
                        <TestTube className="w-4 h-4 mr-1" />
                        Test
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleEditDevice(device)}
                      >
                        <Edit className="w-4 h-4 mr-1" />
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDeleteDevice(device.id)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Delete
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DeviceManager;
