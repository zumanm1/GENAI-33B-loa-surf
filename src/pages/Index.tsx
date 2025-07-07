
import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Activity, 
  Server, 
  Settings, 
  Database, 
  NetworkIcon,
  Zap,
  Shield,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  Clock,
  Download,
  Upload,
  Search
} from 'lucide-react';

import Dashboard from '@/components/Dashboard';
import DeviceManager from '@/components/DeviceManager';
import ConfigRetrieve from '@/components/ConfigRetrieve';
import ConfigPush from '@/components/ConfigPush';
import BackupManager from '@/components/BackupManager';

const Index = () => {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-sm border-b border-slate-200 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-2 rounded-lg">
                <NetworkIcon className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                  Network Automation Platform
                </h1>
                <p className="text-sm text-slate-600">Cisco Router Management & Automation</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                <CheckCircle className="w-3 h-3 mr-1" />
                System Online
              </Badge>
              <Badge variant="outline" className="bg-blue-50 text-blue-700 border-blue-200">
                <Activity className="w-3 h-3 mr-1" />
                EVE-NG Connected
              </Badge>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-5 bg-white/60 backdrop-blur-sm border border-slate-200">
            <TabsTrigger value="dashboard" className="flex items-center space-x-2">
              <TrendingUp className="w-4 h-4" />
              <span>Dashboard</span>
            </TabsTrigger>
            <TabsTrigger value="retrieve" className="flex items-center space-x-2">
              <Download className="w-4 h-4" />
              <span>Config Retrieve</span>
            </TabsTrigger>
            <TabsTrigger value="push" className="flex items-center space-x-2">
              <Upload className="w-4 h-4" />
              <span>Config Push</span>
            </TabsTrigger>
            <TabsTrigger value="backups" className="flex items-center space-x-2">
              <Database className="w-4 h-4" />
              <span>Backups</span>
            </TabsTrigger>
            <TabsTrigger value="devices" className="flex items-center space-x-2">
              <Server className="w-4 h-4" />
              <span>Devices</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="space-y-6">
            <Dashboard />
          </TabsContent>

          <TabsContent value="retrieve" className="space-y-6">
            <ConfigRetrieve />
          </TabsContent>

          <TabsContent value="push" className="space-y-6">
            <ConfigPush />
          </TabsContent>

          <TabsContent value="backups" className="space-y-6">
            <BackupManager />
          </TabsContent>

          <TabsContent value="devices" className="space-y-6">
            <DeviceManager />
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="bg-white/60 backdrop-blur-sm border-t border-slate-200 mt-16">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6 text-sm text-slate-600">
              <span>© 2025 Network Automation Platform</span>
              <span>Hybrid Web + API Architecture</span>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="outline" className="bg-slate-50">
                <Shield className="w-3 h-3 mr-1" />
                Secure
              </Badge>
              <Badge variant="outline" className="bg-slate-50">
                <Zap className="w-3 h-3 mr-1" />
                High Performance
              </Badge>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Index;
