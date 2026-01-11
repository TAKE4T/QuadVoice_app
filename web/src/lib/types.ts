export enum IdentityDocType {
  Skill = "skill",
  Goal = "goal",
  Knowledge = "knowledge",
}

export enum PlatformName {
  Qiita = "qiita",
  Zenn = "zenn",
  Note = "note",
  Owned = "owned",
}

export enum ProjectStatus {
  Processing = "processing",
  Completed = "completed",
  Failed = "failed",
}

export interface GenerateRequest {
  theme: string;
}

export interface GenerateResponse {
  project_id: string;
  status: ProjectStatus;
  preview: Record<string, string>;
}

export interface WorkflowEventResponse {
  node: string;
  message: string;
  status: ProjectStatus;
}

export interface ProjectResultResponse {
  project_id: string;
  theme: string;
  status: ProjectStatus;
  outputs: Record<string, string>;
  events: WorkflowEventResponse[];
}
