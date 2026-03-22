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
}

export interface AppStats {
  total_files: number;
  total_loc: number;
  languages: Record<string, number>;
  hotspots_count: number;
  duplicates_count: number;
}

export interface AppData {
  files: FileNode[];
  stats: AppStats;
}
