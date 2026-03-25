export interface FileNode {
  path: string;
  loc: number;
  lang: string;
  risk: string;
  score: number;
  is_dup: boolean;
  is_gen: boolean;
  functions: { name: string; loc: number }[];
  classes: { name: string; methods: number }[];
  imports: string[];
  radar: number[];
  impact?: { upstream: string[]; downstream: string[]; blast_radius: number; };
  reasons?: string[];
  recommendations?: { issue: string; action: string; }[];
}

export interface AppStats {
  total_files: number;
  total_loc: number;
  languages: Record<string, number>;
  hotspots_count: number;
  duplicates_count: number;
  session_path?: string;
}

export interface Diagrams {
  dependency: string;
  class_diagram: string;
  call_graph: string;
  render_tree: string;
}

export interface HotspotRadarDataset {
  label: string;
  data: number[];
  backgroundColor: string;
  borderColor: string;
}

export interface HotspotRadar {
  datasets: HotspotRadarDataset[];
}

export interface ArchitectureIssue {
  title: string;
  severity: string;
  description: string;
  files: string[];
  recommendation: string;
}

export interface AppData {
  files: FileNode[];
  stats: AppStats;
  diagrams: Diagrams;
  hotspot_radar: HotspotRadar;
  architecture_issues: ArchitectureIssue[];
}
