
import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Activity, 
  Server, 
  Database, 
  Clock,
  CheckCircle,
  AlertCircle,
  TrendingUp,
  Zap,
  Network,
  HardDrive,
  Cpu,
  Wifi
} from 'lucide-react';

interface DeviceStatus {
  name: string;
  status: 'online' | 'offline' | 'warning';
  lastSeen: string;
  uptime: string;
  configBackups: number;
}

const Dashboard = () => {
  const [devices, setDevices] = useState<DeviceStatus[]>([
    { name: 'R15', status: 'online', lastSeen: '2 min ago', uptime: '15d 4h', configBackups: 12 },
    { name: 'R16', status: 'online', lastSeen: '1 min ago', uptime: '15d 4h', configBackups: 8 },
    { name: 'R17', status: 'warning', lastSeen: '10 min ago', uptime: '12d 2h', configBackups: 5 },
    { name: 'R18', status: 'offline', lastSeen: '2h ago', uptime: 'N/A', configBackups: 15 },
    { name: 'R19', status: 'online', lastSeen: '30s ago', uptime: '20d 1h', configBackups: 22 },
    { name: 'R20', status: 'online', lastSeen: '45s ago', uptime: '18d 6h', configBackups: 18 }
  ]);

  const [systemStats, setSystemStats] = useState({
    totalDevices: 6,
    onlineDevices: 4,
    totalBackups: 80,
    automationJobs: 156,
    lastBackup: '5 minutes ago',
    systemUptime: '45 days',
    apiCalls: 1247,
    avgResponseTime: '1.2s'
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'warning':
        return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      case 'offline':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Activity className="w-4 h-4 text-gray-500" />;
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
      default:
        return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  const handleTestAllDevices = async () => {
    console.log('Testing all devices...');
    // API call would go here
  };

  const handleRefreshData = async () => {
    console.log('Refreshing dashboard data...');
    // API call would go here
  };

  return (
    <div className="space-y-6">
      {/* Title and Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-slate-800">Network Dashboard</h2>
          <p className="text-slate-600 mt-1">Real-time monitoring and system overview</p>
        </div>
        <div className="flex space-x-3">
          <Button onClick={handleRefreshData} variant="outline">
            <Activity className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={handleTestAllDevices} className="bg-gradient-to-r from-blue-600 to-indigo-600">
            <Zap className="w-4 h-4 mr-2" />
            Test All Devices
          </Button>
        </div>
      </div>

      {/* System Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-blue-700">Total Devices</CardTitle>
            <Server className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-800">{systemStats.totalDevices}</div>
            <p className="text-xs text-blue-600 mt-1">{systemStats.onlineDevices} online</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-green-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-green-700">Config Backups</CardTitle>
            <Database className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-800">{systemStats.totalBackups}</div>
            <p className="text-xs text-green-600 mt-1">Last: {systemStats.lastBackup}</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-50 to-violet-50 border-purple-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-purple-700">Automation Jobs</CardTitle>
            <TrendingUp className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-800">{systemStats.automationJobs}</div>
            <p className="text-xs text-purple-600 mt-1">Total executed</p>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-orange-50 to-amber-50 border-orange-200">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-orange-700">API Calls</CardTitle>
            <Activity className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-800">{systemStats.apiCalls}</div>
            <p className="text-xs text-orange-600 mt-1">Avg: {systemStats.avgResponseTime}</p>
          </CardContent>
        </Card>
      </div>

      {/* Device Status Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Device List */}
        <Card className="bg-white/80 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Network className="w-5 h-5 text-blue-600" />
              <span>Device Status</span>
            </CardTitle>
            <CardDescription>Real-time status of all network devices</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {devices.map((device) => (
                <div key={device.name} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border">
                  <div className="flex items-center space-x-4">
                    {getStatusIcon(device.status)}
                    <div>
                      <h4 className="font-semibold text-slate-800">{device.name}</h4>
                      <p className="text-xs text-slate-600">Last seen: {device.lastSeen}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    {getStatusBadge(device.status)}
                    <p className="text-xs text-slate-600 mt-1">Uptime: {device.uptime}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* System Health */}
        <Card className="bg-white/80 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="w-5 h-5 text-green-600" />
              <span>System Health</span>
            </CardTitle>
            <CardDescription>Platform performance and resource usage</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="flex items-center space-x-2">
                    <Cpu className="w-4 h-4 text-blue-500" />
                    <span>CPU Usage</span>
                  </span>
                  <span className="font-medium">23%</span>
                </div>
                <Progress value={23} className="h-2" />
              </div>

              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="flex items-center space-x-2">
                    <HardDrive className="w-4 h-4 text-purple-500" />
                    <span>Memory Usage</span>
                  </span>
                  <span className="font-medium">67%</span>
                </div>
                <Progress value={67} className="h-2" />
              </div>

              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="flex items-center space-x-2">
                    <Database className="w-4 h-4 text-green-500" />
                    <span>Database Usage</span>
                  </span>
                  <span className="font-medium">12%</span>
                </div>
                <Progress value={12} className="h-2" />
              </div>

              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="flex items-center space-x-2">
                    <Wifi className="w-4 h-4 text-orange-500" />
                    <span>Network Load</span>
                  </span>
                  <span className="font-medium">45%</span>
                </div>
                <Progress value={45} className="h-2" />
              </div>
            </div>

            <div className="pt-4 border-t border-slate-200">
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center space-x-2">
                  <Clock className="w-4 h-4 text-slate-500" />
                  <span>System Uptime</span>
                </span>
                <span className="font-medium text-green-600">{systemStats.systemUptime}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
        <CardHeader>
          <CardTitle className="text-blue-800">Quick Actions</CardTitle>
          <CardDescription className="text-blue-600">
            Common network operations and shortcuts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button variant="outline" className="h-16 flex-col space-y-2">
              <Database className="w-6 h-6" />
              <span>Backup All Configs</span>
            </Button>
            <Button variant="outline" className="h-16 flex-col space-y-2">
              <Activity className="w-6 h-6" />
              <span>Health Check</span>
            </Button>
            <Button variant="outline" className="h-16 flex-col space-y-2">
              <TrendingUp className="w-6 h-6" />
              <span>View Reports</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;
