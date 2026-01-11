"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { API_BASE_URL, WS_BASE_URL } from "@/lib/config";
import {
  GenerateResponse,
  ProjectStatus,
  WorkflowEventResponse,
} from "@/lib/types";
import {
  Terminal,
  PenTool,
  LayoutTemplate,
  BookOpen,
  Layers,
  Sparkles,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

export default function Home() {
  const [theme, setTheme] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<string>("Ready");
  const [projectId, setProjectId] = useState<string | null>(null);
  const [logs, setLogs] = useState<WorkflowEventResponse[]>([]);
  const [outputs, setOutputs] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState("qiita");

  const wsRef = useRef<WebSocket | null>(null);

  const startGeneration = async () => {
    if (!theme) return;
    setIsGenerating(true);
    setProgress(5);
    setStatus("Initializing...");
    setLogs([]);
    setOutputs({});

    try {
      // 1. Create Project
      const res = await fetch(`${API_BASE_URL}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ theme }),
      });

      if (!res.ok) throw new Error("Failed to start generation");

      const data: GenerateResponse = await res.json();
      setProjectId(data.project_id);
      setStatus("Starting workflow...");
      setProgress(10);

      // 2. Connect WebSocket
      connectWebSocket(data.project_id);
    } catch (error) {
      console.error(error);
      setStatus("Error starting generation");
      setIsGenerating(false);
    }
  };

  const connectWebSocket = (id: string) => {
    if (wsRef.current) wsRef.current.close();

    const wsUrl = `${WS_BASE_URL}/ws/generate/${id}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("Connected to WS");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.node) {
        // Workflow Event
        const eventData = data as WorkflowEventResponse;
        setLogs((prev) => [...prev, eventData]);
        setStatus(`[${eventData.node}] ${eventData.message}`);
        
        // Simple progress simulation based on nodes
        if (eventData.node === "intent_analysis") setProgress(20);
        if (eventData.node === "angle_planning") setProgress(40);
        if (eventData.node === "drafting") setProgress(70);
        if (eventData.node === "refinement") setProgress(90);
      } else if (data.status) {
        // Final Result or Status Update
        if (data.status === ProjectStatus.Completed) {
          setOutputs(data.outputs);
          setProgress(100);
          setStatus("Completed!");
          setIsGenerating(false);
          ws.close();
        } else if (data.status === ProjectStatus.Failed) {
          setStatus("Failed.");
          setIsGenerating(false);
          ws.close();
        }
      } else if (data.error) {
        console.error("WS Error:", data.error);
        setStatus(`Error: ${data.error}`);
        setIsGenerating(false);
        ws.close();
      }
    };

    ws.onerror = (e) => {
      console.error("WebSocket error", e);
      setStatus("WebSocket connection error");
      setIsGenerating(false);
    };

    wsRef.current = ws;
  };

  // Cleanup WS on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 p-8 font-sans">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Header */}
        <div className="flex items-center space-x-4">
          <div className="bg-primary/10 p-3 rounded-lg">
            <Sparkles className="h-8 w-8 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-slate-900">
              QuadVoice
            </h1>
            <p className="text-slate-500">
              Adaptive Content Generation Platform
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Left Column: Controls & Input */}
          <div className="lg:col-span-1 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Generation Settings</CardTitle>
                <CardDescription>
                  Define your theme and thought process.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="theme">Theme / Topic</Label>
                  <Input
                    id="theme"
                    placeholder="e.g. The future of AI Agents"
                    value={theme}
                    onChange={(e) => setTheme(e.target.value)}
                    disabled={isGenerating}
                  />
                </div>
                <Button
                  className="w-full"
                  onClick={startGeneration}
                  disabled={isGenerating || !theme}
                >
                  {isGenerating ? (
                    <>
                      <Layers className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <PenTool className="mr-2 h-4 w-4" />
                      Generate Content
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Identity Management (Stub) */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5" />
                  Identity Maps
                </CardTitle>
                <CardDescription>
                  Your thoughts and knowledge base.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="text-sm text-slate-500 mb-4">
                  Currently using 3 ingested files from server.
                </div>
                <Button variant="outline" className="w-full" disabled>
                  Manage Identity (Coming Soon)
                </Button>
              </CardContent>
            </Card>

            {/* Logs / Status */}
            <Card className="h-[400px] flex flex-col">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Terminal className="h-4 w-4" />
                  Workflow Logs
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto font-mono text-xs bg-slate-950 text-slate-300 m-4 rounded p-4 space-y-2">
                {logs.length === 0 && (
                  <div className="text-slate-600">Waiting for events...</div>
                )}
                {logs.map((log, i) => (
                  <div key={i} className="border-l-2 border-slate-700 pl-2">
                    <span className="text-blue-400">[{log.node}]</span>{" "}
                    {log.message}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Right Column: Output & Preview */}
          <div className="lg:col-span-2 space-y-6">
            {isGenerating || Object.keys(outputs).length > 0 ? (
              <div className="space-y-4">
                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">{status}</span>
                    <span className="text-slate-500">{progress}%</span>
                  </div>
                  <Progress value={progress} className="h-2" />
                </div>

                {/* Results Tabs */}
                <Tabs
                  value={activeTab}
                  onValueChange={setActiveTab}
                  className="w-full"
                >
                  <TabsList className="grid w-full grid-cols-4">
                    <TabsTrigger value="qiita">Qiita</TabsTrigger>
                    <TabsTrigger value="zenn">Zenn</TabsTrigger>
                    <TabsTrigger value="note">note</TabsTrigger>
                    <TabsTrigger value="owned">Owned</TabsTrigger>
                  </TabsList>
                  {["qiita", "zenn", "note", "owned"].map((platform) => (
                    <TabsContent key={platform} value={platform}>
                      <Card>
                        <CardHeader>
                          <CardTitle className="capitalize flex justify-between">
                            {platform} Article
                            {outputs[platform] && (
                             <CheckCircle2 className="text-green-500 h-5 w-5"/>
                            )}
                          </CardTitle>
                          <CardDescription>
                             Optimized structure and tone for {platform}.
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <Textarea
                            className="min-h-[500px] font-mono text-sm leading-relaxed"
                            value={outputs[platform] || "Waiting for content..."}
                            readOnly
                          />
                        </CardContent>
                      </Card>
                    </TabsContent>
                  ))}
                </Tabs>
              </div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-slate-400 space-y-4 border-2 border-dashed border-slate-200 rounded-xl p-12">
                <LayoutTemplate className="h-16 w-16 opacity-20" />
                <p>Enter a theme to generate content across 4 platforms.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
