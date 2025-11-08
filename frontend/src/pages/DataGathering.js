import React, { useEffect, useState } from 'react';
import { territoryAPI, dataGatheringAPI } from '../lib/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { FileText, Send, Calendar } from 'lucide-react';
import { motion } from 'framer-motion';

export const DataGathering = () => {
  const [territories, setTerritories] = useState([]);
  const [selectedTerritory, setSelectedTerritory] = useState('');
  const [gatheredData, setGatheredData] = useState([]);
  const [formData, setFormData] = useState({
    propertyValue: '',
    rentPrice: '',
    occupancyRate: '',
    maintenanceCost: '',
    tenantType: '',
    notes: ''
  });

  useEffect(() => {
    loadTerritories();
  }, []);

  useEffect(() => {
    if (selectedTerritory) {
      loadGatheredData();
    }
  }, [selectedTerritory]);

  const loadTerritories = async () => {
    try {
      const response = await territoryAPI.getAll();
      setTerritories(response.data);
    } catch (error) {
      toast.error('Failed to load territories');
    }
  };

  const loadGatheredData = async () => {
    try {
      const response = await dataGatheringAPI.getByTerritory(selectedTerritory);
      setGatheredData(response.data);
    } catch (error) {
      console.error('Failed to load gathered data:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedTerritory) {
      toast.error('Please select a territory');
      return;
    }

    try {
      await dataGatheringAPI.submit({
        territoryId: selectedTerritory,
        data: formData,
        submittedBy: 'current_user'
      });
      toast.success('Data submitted successfully!');
      setFormData({
        propertyValue: '',
        rentPrice: '',
        occupancyRate: '',
        maintenanceCost: '',
        tenantType: '',
        notes: ''
      });
      loadGatheredData();
    } catch (error) {
      toast.error('Failed to submit data');
    }
  };

  return (
    <div className="p-6 space-y-6" data-testid="data-gathering-page">
      <div>
        <h1 className="text-3xl font-bold">Data Gathering</h1>
        <p className="text-muted-foreground mt-1">Collect live data from users for territory analysis</p>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        {/* Data Collection Form */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Submit Data
              </CardTitle>
              <CardDescription>
                Contribute live data for territory insights
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="territory">Select Territory *</Label>
                  <Select value={selectedTerritory} onValueChange={setSelectedTerritory}>
                    <SelectTrigger data-testid="territory-select">
                      <SelectValue placeholder="Choose a territory" />
                    </SelectTrigger>
                    <SelectContent>
                      {territories.map((territory) => (
                        <SelectItem key={territory.id} value={territory.id}>
                          {territory.name} - {territory.city}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="propertyValue">Property Value (₹)</Label>
                    <Input
                      id="propertyValue"
                      type="number"
                      data-testid="property-value-input"
                      value={formData.propertyValue}
                      onChange={(e) => setFormData({ ...formData, propertyValue: e.target.value })}
                      placeholder="5000000"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="rentPrice">Rent Price (₹/month)</Label>
                    <Input
                      id="rentPrice"
                      type="number"
                      value={formData.rentPrice}
                      onChange={(e) => setFormData({ ...formData, rentPrice: e.target.value })}
                      placeholder="25000"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="occupancyRate">Occupancy Rate (%)</Label>
                    <Input
                      id="occupancyRate"
                      type="number"
                      min="0"
                      max="100"
                      value={formData.occupancyRate}
                      onChange={(e) => setFormData({ ...formData, occupancyRate: e.target.value })}
                      placeholder="85"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="maintenanceCost">Maintenance Cost (₹/month)</Label>
                    <Input
                      id="maintenanceCost"
                      type="number"
                      value={formData.maintenanceCost}
                      onChange={(e) => setFormData({ ...formData, maintenanceCost: e.target.value })}
                      placeholder="5000"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="tenantType">Tenant Type</Label>
                  <Select value={formData.tenantType} onValueChange={(value) => setFormData({ ...formData, tenantType: value })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select tenant type" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="family">Family</SelectItem>
                      <SelectItem value="bachelor">Bachelor</SelectItem>
                      <SelectItem value="pg">PG</SelectItem>
                      <SelectItem value="commercial">Commercial</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="notes">Additional Notes</Label>
                  <textarea
                    id="notes"
                    className="w-full min-h-[100px] rounded-md border border-input bg-background px-3 py-2 text-sm"
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    placeholder="Any additional information..."
                  />
                </div>

                <Button type="submit" className="w-full" data-testid="submit-data-button">
                  <Send className="w-4 h-4 mr-2" />
                  Submit Data
                </Button>
              </form>
            </CardContent>
          </Card>
        </motion.div>

        {/* Submitted Data */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
        >
          <Card>
            <CardHeader>
              <CardTitle>Submitted Data</CardTitle>
              <CardDescription>
                {selectedTerritory
                  ? `Data entries for ${territories.find(t => t.id === selectedTerritory)?.name || 'selected territory'}`
                  : 'Select a territory to view submissions'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 max-h-[600px] overflow-y-auto">
                {gatheredData.length > 0 ? (
                  gatheredData.map((entry, index) => (
                    <div key={entry.id} className="p-4 border rounded-lg space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">Entry #{index + 1}</span>
                        <span className="text-xs text-muted-foreground flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {new Date(entry.timestamp).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        {entry.data.propertyValue && (
                          <div>
                            <span className="text-muted-foreground">Property Value:</span>
                            <span className="ml-2 font-medium">₹{parseInt(entry.data.propertyValue).toLocaleString()}</span>
                          </div>
                        )}
                        {entry.data.rentPrice && (
                          <div>
                            <span className="text-muted-foreground">Rent:</span>
                            <span className="ml-2 font-medium">₹{parseInt(entry.data.rentPrice).toLocaleString()}</span>
                          </div>
                        )}
                        {entry.data.occupancyRate && (
                          <div>
                            <span className="text-muted-foreground">Occupancy:</span>
                            <span className="ml-2 font-medium">{entry.data.occupancyRate}%</span>
                          </div>
                        )}
                        {entry.data.tenantType && (
                          <div>
                            <span className="text-muted-foreground">Tenant Type:</span>
                            <span className="ml-2 font-medium capitalize">{entry.data.tenantType}</span>
                          </div>
                        )}
                      </div>
                      {entry.data.notes && (
                        <p className="text-sm text-muted-foreground italic">{entry.data.notes}</p>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    {selectedTerritory
                      ? 'No data submitted yet for this territory'
                      : 'Select a territory to view submissions'}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
};