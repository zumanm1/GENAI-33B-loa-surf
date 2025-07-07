
import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { 
  Upload, 
  Send, 
  AlertTriangle, 
  CheckCircle,
  Clock,
  Server,
  FileText,
  Settings,
  Zap,
  Shield
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface DeploymentJob {
  id: string;
  device: string;
  status: 'pending' | 'running' | 'success' | 'failed' | 'warning';
  progress: number;
  message: string;
  startTime: string;
  endTime?: string;
}

const ConfigPush = () => {
  const { toast } = useToast();
  const [selectedDevices, setSelectedDevices] = useState<string[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [configCommands, setConfigCommands] = useState('');
  const [selectedMethod, setSelectedMethod] = useState('netmiko');
  const [isDeploying, setIsDeploying] = useState(false);
  const [validateOnly, setValidateOnly] = useState(false);
  const [deploymentJobs, setDeploymentJobs] = useState<DeploymentJob[]>([]);

  const devices = [
    { value: 'R15', label: 'R15 - Core Router', status: 'online' },
    { value: 'R16', label: 'R16 - Distribution', status: 'online' },
    { value: 'R17', label: 'R17 - Access Layer', status: 'warning' },
    { value: 'R18', label: 'R18 - Border Router', status: 'offline' },
    { value: 'R19', label: 'R19 - MPLS PE', status: 'online' },
    { value: 'R20', label: 'R20 - Backup Core', status: 'online' }
  ];

  const templates = [
    { value: 'interface_basic', label: 'Basic Interface Configuration' },
    { value: 'vlan_setup', label: 'VLAN Configuration' },
    { value: 'routing_ospf', label: 'OSPF Routing Setup' },
    { value: 'security_acl', label: 'Security ACL Template' },
    { value: 'qos_policy', label: 'QoS Policy Configuration' },
    { value: 'custom', label: 'Custom Configuration' }
  ];

  const methods = [
    { value: 'netmiko', label: 'Netmiko', description: 'Fast deployment' },
    { value: 'napalm', label: 'NAPALM', description: 'With rollback' },
    { value: 'nornir', label: 'Nornir', description: 'Parallel execution' }
  ];

  const templateConfigs = {
    'interface_basic': `interface GigabitEthernet0/1
 description {{ description | default("Configured via automation") }}
 ip address {{ ip_address }} {{ subnet_mask }}
 no shutdown
 duplex auto
 speed auto`,
    'vlan_setup': `vlan {{ vlan_id }}
 name {{ vlan_name }}
!
interface vlan{{ vlan_id }}
 ip address {{ gateway_ip }} {{ subnet_mask }}
 no shutdown`,
    'routing_ospf': `router ospf {{ process_id }}
 network {{ network }} {{ wildcard }} area {{ area }}
 router-id {{ router_id }}
 passive-interface default
 no passive-interface {{ active_interface }}`,
    'security_acl': `ip access-list extended {{ acl_name }}
 permit tcp {{ source_network }} {{ destination_network }} eq {{ port }}
 deny ip any any log
!
interface {{ interface }}
 ip access-group {{ acl_name }} {{ direction }}`,
    'qos_policy': `class-map match-all {{ class_name }}
 match dscp {{ dscp_value }}
!
policy-map {{ policy_name }}
 class {{ class_name }}
  bandwidth percent {{ bandwidth_percent }}`
  };

  const handleTemplateChange = (template: string) => {
    setSelectedTemplate(template);
    if (template !== 'custom' && templateConfigs[template as keyof typeof templateConfigs]) {
      setConfigCommands(templateConfigs[template as keyof typeof templateConfigs]);
    } else if (template === 'custom') {
      setConfigCommands('');
    }
  };

  const handleDeviceToggle = (deviceValue: string) => {
    setSelectedDevices(prev => 
      prev.includes(deviceValue) 
        ? prev.filter(d => d !== deviceValue)
        : [...prev, deviceValue]
    );
  };

  const handleDeployConfiguration = async () => {
    if (!selectedDevices.length || !configCommands.trim()) {
      toast({
        title: "Validation Error",
        description: "Please select devices and provide configuration commands",
        variant: "destructive"
      });
      return;
    }

    setIsDeploying(true);
    
    // Initialize deployment jobs
    const jobs: DeploymentJob[] = selectedDevices.map((device, index) => ({
      id: `job_${Date.now()}_${index}`,
      device,
      status: 'pending',
      progress: 0,
      message: 'Initializing deployment...',
      startTime: new Date().toISOString()
    }));
    
    setDeploymentJobs(jobs);

    try {
      // Simulate deployment process
      for (let i = 0; i < jobs.length; i++) {
        const job = jobs[i];
        
        // Update job to running
        setDeploymentJobs(prev => prev.map(j => 
          j.id === job.id ? { ...j, status: 'running', message: 'Connecting to device...' } : j
        ));
        
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Simulate progress updates
        for (let progress = 20; progress <= 100; progress += 20) {
          setDeploymentJobs(prev => prev.map(j => 
            j.id === job.id ? { 
              ...j, 
              progress, 
              message: getProgressMessage(progress)
            } : j
          ));
          await new Promise(resolve => setTimeout(resolve, 800));
        }
        
        // Simulate random success/failure
        const isSuccess = Math.random() > 0.2; // 80% success rate
        
        setDeploymentJobs(prev => prev.map(j => 
          j.id === job.id ? {
            ...j,
            status: isSuccess ? 'success' : 'failed',
            progress: 100,
            message: isSuccess ? 'Configuration deployed successfully' : 'Failed to deploy configuration',
            endTime: new Date().toISOString()
          } : j
        ));
        
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      
      const successCount = jobs.filter(j => Math.random() > 0.2).length;
      
      toast({
        title: "Deployment Complete",
        description: `${successCount}/${jobs.length} devices configured successfully`,
      });
      
    } catch (error) {
      toast({
        title: "Deployment Error",
        description: "Failed to deploy configuration",
        variant: "destructive"
      });
    } finally {
      setIsDeploying(false);
    }
  };

  const getProgressMessage = (progress: number): string => {
    switch (progress) {
      case 20: return 'Establishing connection...';
      case 40: return 'Validating configuration...';
      case 60: return 'Applying configuration...';
      case 80: return 'Verifying changes...';
      case 100: return 'Deployment complete';
      default: return 'Processing...';
    }
  };

  const getJobStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'running':
        return <Clock className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  const getJobStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge className="bg-green-100 text-green-800 border-green-200">Success</Badge>;
      case 'failed':
        return <Badge className="bg-red-100 text-red-800 border-red-200">Failed</Badge>;
      case 'running':
        return <Badge className="bg-blue-100 text-blue-800 border-blue-200">Running</Badge>;
      case 'warning':
        return <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200">Warning</Badge>;
      case 'pending':
        return <Badge className="bg-gray-100 text-gray-800 border-gray-200">Pending</Badge>;
      default:
        return <Badge variant="secondary">Unknown</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-3xl font-bold text-slate-800">Configuration Push</h2>
        <p className="text-slate-600 mt-1">Deploy configurations to network devices with templates and validation</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Configuration Form */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Settings className="w-5 h-5 text-blue-600" />
                <span>Deployment Configuration</span>
              </CardTitle>
              <CardDescription>Configure your deployment settings and target devices</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Device Selection */}
              <div className="space-y-3">
                <Label>Target Devices</Label>
                <div className="grid grid-cols-2 gap-3">
                  {devices.map((device) => (
                    <div
                      key={device.value}
                      className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                        selectedDevices.includes(device.value)
                          ? 'bg-blue-50 border-blue-300'
                          : 'bg-white border-gray-200 hover:bg-gray-50'
                      } ${device.status === 'offline' ? 'opacity-50' : ''}`}
                      onClick={() => device.status !== 'offline' && handleDeviceToggle(device.value)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            checked={selectedDevices.includes(device.value)}
                            onChange={() => {}}
                            disabled={device.status === 'offline'}
                            className="rounded border-gray-300"
                          />
                          <span className={`font-medium ${device.status === 'offline' ? 'text-gray-400' : 'text-gray-800'}`}>
                            {device.value}
                          </span>
                        </div>
                        <Badge 
                          variant="outline" 
                          className={
                            device.status === 'online' ? 'bg-green-50 text-green-700 border-green-200' :
                            device.status === 'warning' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                            'bg-red-50 text-red-700 border-red-200'
                          }
                        >
                          {device.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Template Selection */}
              <div className="space-y-2">
                <Label htmlFor="template">Configuration Template</Label>
                <Select value={selectedTemplate} onValueChange={handleTemplateChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a template or create custom" />
                  </SelectTrigger>
                  <SelectContent>
                    {templates.map((template) => (
                      <SelectItem key={template.value} value={template.value}>
                        {template.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Method Selection */}
              <div className="space-y-2">
                <Label htmlFor="method">Deployment Method</Label>
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
                    id="validateOnly"
                    checked={validateOnly}
                    onChange={(e) => setValidateOnly(e.target.checked)}
                    className="rounded border-gray-300"
                  />
                  <Label htmlFor="validateOnly" className="text-sm">
                    Validate only (dry run)
                  </Label>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Configuration Editor */}
          <Card className="bg-white/80 backdrop-blur-sm">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <FileText className="w-5 h-5 text-green-600" />
                <span>Configuration Commands</span>
              </CardTitle>
              <CardDescription>
                {selectedTemplate && selectedTemplate !== 'custom' 
                  ? 'Template loaded - modify as needed or use Jinja2 variables'
                  : 'Enter your configuration commands'
                }
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Textarea
                value={configCommands}
                onChange={(e) => setConfigCommands(e.target.value)}
                placeholder="Enter configuration commands here..."
                rows={12}
                className="font-mono text-sm"
              />
              {selectedTemplate && selectedTemplate !== 'custom' && (
                <div className="mt-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-700">
                    <span className="font-medium">Template variables:</span> Use Jinja2 syntax like 
                    <code className="mx-1 px-1 bg-blue-100 rounded">{'{{ ip_address }}'}</code> for dynamic values
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Deploy Button */}
          <Button 
            onClick={handleDeployConfiguration}
            disabled={isDeploying || !selectedDevices.length || !configCommands.trim()}
            className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-lg py-6"
          >
            {isDeploying ? (
              <>
                <Clock className="w-5 h-5 mr-2 animate-spin" />
                Deploying Configuration...
              </>
            ) : validateOnly ? (
              <>
                <Shield className="w-5 h-5 mr-2" />
                Validate Configuration
              </>
            ) : (
              <>
                <Send className="w-5 h-5 mr-2" />
                Deploy to {selectedDevices.length} Device{selectedDevices.length !== 1 ? 's' : ''}
              </>
            )}
          </Button>
        </div>

        {/* Deployment Status */}
        <Card className="bg-white/80 backdrop-blur-sm">
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Zap className="w-5 h-5 text-purple-600" />
              <span>Deployment Status</span>
            </CardTitle>
            <CardDescription>
              {deploymentJobs.length > 0 
                ? `Tracking ${deploymentJobs.length} deployment jobs`
                : 'Status will appear here during deployment'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {deploymentJobs.length > 0 ? (
              <div className="space-y-4">
                {deploymentJobs.map((job) => (
                  <div key={job.id} className="p-4 bg-slate-50 rounded-lg border">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        {getJobStatusIcon(job.status)}
                        <span className="font-medium">{job.device}</span>
                      </div>
                      {getJobStatusBadge(job.status)}
                    </div>
                    
                    {job.status === 'running' && (
                      <div className="mb-2">
                        <Progress value={job.progress} className="h-2" />
                      </div>
                    )}
                    
                    <p className="text-sm text-slate-600">{job.message}</p>
                    
                    <div className="text-xs text-slate-500 mt-2">
                      Started: {new Date(job.startTime).toLocaleTimeString()}
                      {job.endTime && (
                        <span className="ml-2">
                          Completed: {new Date(job.endTime).toLocaleTimeString()}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-slate-500 py-8">
                <Upload className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No active deployments</p>
                <p className="text-xs mt-1">Status will appear here when you start a deployment</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ConfigPush;
