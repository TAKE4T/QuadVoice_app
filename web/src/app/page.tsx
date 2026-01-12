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
  IdentityDocType,
} from "@/lib/types";
import {
  Terminal,
  PenTool,
  LayoutTemplate,
  BookOpen,
  Layers,
  Sparkles,
  CheckCircle2,
  FileUp,
} from "lucide-react";

export default function Home() {
  const [theme, setTheme] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<string>("準備完了");
  const [projectId, setProjectId] = useState<string | null>(null);
  const [logs, setLogs] = useState<WorkflowEventResponse[]>([]);
  const [outputs, setOutputs] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState("qiita");

  // Knowledge Map state
  const [knowledgeContent, setKnowledgeContent] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState("");

  const wsRef = useRef<WebSocket | null>(null);

  const startGeneration = async () => {
    if (!theme) return;
    setIsGenerating(true);
    setProgress(5);
    setStatus("初期化中...");
    setLogs([]);
    setOutputs({});

    try {
      // 1. Create Project
      const res = await fetch(`${API_BASE_URL}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ theme }),
      });

      if (!res.ok) throw new Error("生成の開始に失敗しました");

      const data: GenerateResponse = await res.json();
      setProjectId(data.project_id);
      setStatus("ワークフローを開始中...");
      setProgress(10);

      // 2. Connect WebSocket
      connectWebSocket(data.project_id);
    } catch (error) {
      console.error(error);
      setStatus("生成の開始エラー");
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
          setStatus("完了しました！");
          setIsGenerating(false);
          ws.close();
        } else if (data.status === ProjectStatus.Failed) {
          setStatus("失敗しました。");
          setIsGenerating(false);
          ws.close();
        }
      } else if (data.error) {
        console.error("WS Error:", data.error);
        setStatus(`エラー: ${data.error}`);
        setIsGenerating(false);
        ws.close();
      }
    };

    ws.onerror = (e) => {
      console.error("WebSocket error", e);
      setStatus("WebSocket接続エラー");
      setIsGenerating(false);
    };

    wsRef.current = ws;
  };

  const uploadKnowledge = async () => {
    if (!knowledgeContent) return;
    setIsUploading(true);
    setUploadStatus("アップロード中...");

    try {
      const blob = new Blob([knowledgeContent], { type: "text/plain" });
      const file = new File([blob], "knowledge_map.md", { type: "text/markdown" });

      const formData = new FormData();
      formData.append("doc_type", IdentityDocType.Knowledge);
      formData.append("files", file);

      const res = await fetch(`${API_BASE_URL}/ingest/identity`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("アップロードに失敗しました");

      setUploadStatus("保存しました");
      setKnowledgeContent("");
      setTimeout(() => setUploadStatus(""), 3000);
    } catch (error) {
      console.error(error);
      setUploadStatus("エラーが発生しました");
    } finally {
      setIsUploading(false);
    }
  };

  // Cleanup WS on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 p-8 font-sans text-slate-900">
      <div className="mx-auto max-w-6xl space-y-8">
        {/* Header */}
        <div className="flex items-center space-x-4">
          <div className="bg-primary/10 p-3 rounded-lg">
            <Sparkles className="h-8 w-8 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">
              QuadVoice
            </h1>
            <p className="text-slate-500">
              適応型コンテンツ生成プラットフォーム
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
          {/* Left Column: Controls & Input */}
          <div className="lg:col-span-1 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>生成設定</CardTitle>
                <CardDescription>
                  テーマと思想プロセスを定義します。
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="theme">テーマ / トピック</Label>
                  <Input
                    id="theme"
                    placeholder="例: AIエージェントの未来"
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
                      生成中...
                    </>
                  ) : (
                    <>
                      <PenTool className="mr-2 h-4 w-4" />
                      コンテンツ生成
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>

            {/* Identity Management - Knowledge Map Input */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5" />
                  知識マップ (Identity Map)
                </CardTitle>
                <CardDescription>
                  用語集や独自の定義を入力してください。
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="knowledge">知識マップの内容</Label>
                  <Textarea 
                    id="knowledge" 
                    placeholder="# 用語集&#13;&#10;- QuadVoice: 適応型コンテンツ生成システム..." 
                    className="min-h-[150px] font-mono text-xs"
                    value={knowledgeContent}
                    onChange={(e) => setKnowledgeContent(e.target.value)}
                  />
                </div>
                <div className="flex items-center justify-between">
                   <div className="text-sm text-green-600 font-medium">{uploadStatus}</div>
                   <Button 
                     variant="outline" 
                     onClick={uploadKnowledge} 
                     disabled={isUploading || !knowledgeContent}
                     size="sm"
                   >
                    {isUploading ? "送信中..." : <><FileUp className="mr-2 h-4 w-4"/> 保存</>}
                   </Button>
                </div>
              </CardContent>
            </Card>

            {/* Logs / Status */}
            <Card className="h-[400px] flex flex-col">
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Terminal className="h-4 w-4" />
                  ワークフローログ
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 overflow-y-auto font-mono text-xs bg-slate-950 text-slate-300 m-4 rounded p-4 space-y-2">
                {logs.length === 0 && (
                  <div className="text-slate-600">イベント待機中...</div>
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
                            {platform} 記事
                            {outputs[platform] && (
                             <CheckCircle2 className="text-green-500 h-5 w-5"/>
                            )}
                          </CardTitle>
                          <CardDescription>
                             {platform}向けに最適化された構成とトーン。
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <Textarea
                            className="min-h-[500px] font-mono text-sm leading-relaxed"
                            value={outputs[platform] || "コンテンツを待機中..."}
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
                <p>テーマを入力して4つのプラットフォーム向けコンテンツを生成します。</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
