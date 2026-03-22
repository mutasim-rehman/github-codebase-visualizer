import { useMemo, useState } from 'react';
import type { AppData, FileNode } from '../types';
import { ChevronRight, ChevronDown, Folder, FolderOpen, FileCode } from 'lucide-react';

interface SidebarProps {
  data: AppData;
  selected: FileNode | null;
  onSelect: (f: FileNode | null) => void;
}

type TreeEntry = Record<string, any>;

function buildTree(files: FileNode[]): TreeEntry {
  const root: TreeEntry = {};
  files.forEach(f => {
    const parts = f.path.replace(/\\/g, '/').split('/');
    let cur = root;
    parts.forEach((part, i) => {
      if (i === parts.length - 1) {
        cur[part] = f;
      } else {
        cur[part] = cur[part] ?? {};
        cur = cur[part];
      }
    });
  });
  return root;
}

function riskDotClass(file: FileNode) {
  if (file.is_dup) return 'Dup';
  return file.risk;
}

interface NodeProps {
  name: string;
  node: FileNode | TreeEntry;
  depth: number;
  selected: FileNode | null;
  onSelect: (f: FileNode | null) => void;
  pathStr: string;
}

function TreeNode({ name, node, depth, selected, onSelect, pathStr }: NodeProps) {
  const isFile = 'loc' in (node as any);
  const [open, setOpen] = useState(depth === 0);

  if (isFile) {
    const file = node as FileNode;
    const isActive = selected?.path === file.path;
    return (
      <div
        className={`tree-row${isActive ? ' active' : ''}`}
        style={{ paddingLeft: `${16 + depth * 14}px` }}
        onClick={() => onSelect(file)}
        title={file.path}
      >
        <FileCode size={13} className="tree-file-icon" />
        <span className="tree-name">{name}</span>
        <div className={`risk-dot ${riskDotClass(file)}`} title={`Risk: ${file.risk}`} />
      </div>
    );
  }

  const children = node as TreeEntry;
  const keys = Object.keys(children).sort((a, b) => {
    const aIsFile = 'loc' in (children[a] as any);
    const bIsFile = 'loc' in (children[b] as any);
    if (aIsFile !== bIsFile) return aIsFile ? 1 : -1;
    return a.localeCompare(b);
  });

  return (
    <div>
      <div
        className="tree-row"
        style={{ paddingLeft: `${16 + depth * 14}px` }}
        onClick={() => setOpen(o => !o)}
      >
        {open
          ? <ChevronDown size={12} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
          : <ChevronRight size={12} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
        }
        {open
          ? <FolderOpen size={13} className="tree-folder-icon" />
          : <Folder size={13} className="tree-folder-icon" />
        }
        <span className="tree-name" style={{ fontWeight: 500 }}>{name}</span>
      </div>
      {open && keys.map(k => (
        <TreeNode
          key={`${pathStr}/${k}`}
          name={k}
          node={children[k]}
          depth={depth + 1}
          selected={selected}
          onSelect={onSelect}
          pathStr={`${pathStr}/${k}`}
        />
      ))}
    </div>
  );
}

export default function Sidebar({ data, selected, onSelect }: SidebarProps) {
  const tree = useMemo(() => buildTree(data.files), [data.files]);

  const keys = Object.keys(tree).sort((a, b) => {
    const aF = 'loc' in (tree[a] as any);
    const bF = 'loc' in (tree[b] as any);
    if (aF !== bF) return aF ? 1 : -1;
    return a.localeCompare(b);
  });

  return (
    <aside className="sidebar">
      <div className="sidebar-head">
        Files ({data.files.length})
      </div>
      <div className="file-tree">
        {keys.map(k => (
          <TreeNode
            key={k}
            name={k}
            node={tree[k]}
            depth={0}
            selected={selected}
            onSelect={onSelect}
            pathStr={k}
          />
        ))}
      </div>
    </aside>
  );
}
