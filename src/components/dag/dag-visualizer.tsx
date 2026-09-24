import { useMemo, useRef, useState, useEffect } from "react";
import { Link } from "@tanstack/react-router";
import {
  ExternalLink,
  GitBranch,
  Layers,
  Maximize2,
  Minimize2,
  RotateCcw,
  Search,
  ZoomIn,
  ZoomOut,
  Info,
} from "lucide-react";
import type { DependencyDag } from "@/lib/contracts";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface DagVisualizerProps {
  dag: DependencyDag;
  initialSelectedId?: string | undefined;
  onSelectNode?: ((nodeId: string) => void) | undefined;
  height?: number | string | undefined;
}

export function DagVisualizer({
  dag,
  initialSelectedId,
  onSelectNode,
  height = 560,
}: DagVisualizerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [selectedId, setSelectedId] = useState<string | null>(
    initialSelectedId ?? dag.nodes[0]?.id ?? null,
  );
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 40, y: 40 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Sync initialSelectedId
  useEffect(() => {
    if (initialSelectedId) setSelectedId(initialSelectedId);
  }, [initialSelectedId]);

  // Layout calculation
  const { nodeMap, layerGroups, positionedNodes, positionedEdges, bounds } = useMemo(() => {
    const nodeMap = new Map<string, { id: string; number: string; layer: number }>();
    const layerGroups: Record<number, Array<{ id: string; number: string; layer: number }>> = {};

    dag.nodes.forEach((n) => {
      nodeMap.set(n.id, n);
      const group = layerGroups[n.layer] ?? (layerGroups[n.layer] = []);
      group.push(n);
    });

    const NODE_WIDTH = 130;
    const NODE_HEIGHT = 44;
    const LAYER_GAP = 180;
    const NODE_GAP_Y = 64;

    const positionedNodes: Record<
      string,
      { x: number; y: number; width: number; height: number; number: string; layer: number }
    > = {};

    let maxY = 0;
    let maxX = 0;

    Object.entries(layerGroups).forEach(([layerStr, nodesInLayer]) => {
      const layer = Number(layerStr);
      const x = layer * LAYER_GAP + 60;
      if (x + NODE_WIDTH > maxX) maxX = x + NODE_WIDTH;

      nodesInLayer.forEach((n, idx) => {
        const y = idx * NODE_GAP_Y + 60;
        if (y + NODE_HEIGHT > maxY) maxY = y + NODE_HEIGHT;
        positionedNodes[n.id] = {
          x,
          y,
          width: NODE_WIDTH,
          height: NODE_HEIGHT,
          number: n.number,
          layer: n.layer,
        };
      });
    });

    const positionedEdges = dag.edges
      .map((e) => {
        const source = positionedNodes[e.from];
        const target = positionedNodes[e.to];
        if (!source || !target) return null;
        return {
          id: `${e.from}->${e.to}`,
          from: e.from,
          to: e.to,
          type: e.type,
          relationship: e.relationship,
          x1: source.x + source.width,
          y1: source.y + source.height / 2,
          x2: target.x,
          y2: target.y + target.height / 2,
        };
      })
      .filter(Boolean);

    return {
      nodeMap,
      layerGroups,
      positionedNodes,
      positionedEdges,
      bounds: { width: Math.max(800, maxX + 100), height: Math.max(500, maxY + 100) },
    };
  }, [dag]);

  // Compute dependency highlights
  const highlighted = useMemo(() => {
    const active = hoveredId || selectedId;
    if (!active) return { nodes: new Set<string>(), edges: new Set<string>(), up: [], down: [] };

    const activeNodes = new Set<string>([active]);
    const activeEdges = new Set<string>();
    const up: string[] = [];
    const down: string[] = [];

    dag.edges.forEach((e) => {
      if (e.from === active) {
        activeNodes.add(e.to);
        activeEdges.add(`${e.from}->${e.to}`);
        const n = nodeMap.get(e.to);
        if (n) up.push(n.number);
      }
      if (e.to === active) {
        activeNodes.add(e.from);
        activeEdges.add(`${e.from}->${e.to}`);
        const n = nodeMap.get(e.from);
        if (n) down.push(n.number);
      }
    });

    return { nodes: activeNodes, edges: activeEdges, up, down };
  }, [dag, selectedId, hoveredId, nodeMap]);

  // Pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
  };

  const handleMouseUp = () => setIsDragging(false);

  const resetView = () => {
    setZoom(1);
    setPan({ x: 40, y: 40 });
  };

  const fitToScreen = () => {
    if (!containerRef.current) return;
    const { clientWidth, clientHeight } = containerRef.current;
    const scaleX = (clientWidth - 80) / bounds.width;
    const scaleY = (clientHeight - 80) / bounds.height;
    const fitZoom = Math.min(Math.max(0.4, Math.min(scaleX, scaleY)), 1.2);
    setZoom(fitZoom);
    setPan({ x: 40, y: 40 });
  };

  const selectedNode = selectedId ? nodeMap.get(selectedId) : null;

  return (
    <div className="intel-card relative overflow-hidden select-none border border-border/80">
      {/* Visualizer Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border/70 bg-card/80 p-3 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <span className="grid size-7 place-items-center rounded-md bg-accent/30 text-accent-foreground">
            <GitBranch className="size-4" />
          </span>
          <span className="text-xs font-bold uppercase tracking-wider text-primary">
            Normative Dependency DAG
          </span>
          <span className="rounded bg-muted px-2 py-0.5 font-mono text-[10px] text-muted-foreground">
            {dag.stats.nodes} Standards · {dag.stats.normative_edges} Edges · Depth{" "}
            {dag.stats.max_layer}
          </span>
        </div>

        {/* Search & Zoom Controls */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(e) => {
                const val = e.target.value;
                setSearch(val);
                const match = dag.nodes.find((n) =>
                  n.number.toLowerCase().includes(val.toLowerCase()),
                );
                if (match) {
                  setSelectedId(match.id);
                  onSelectNode?.(match.id);
                }
              }}
              placeholder="Jump to IS standard..."
              className="h-8 w-36 pl-8 text-xs bg-background sm:w-48"
            />
          </div>

          <div className="flex items-center rounded-lg border border-border bg-background p-0.5">
            <Button
              variant="ghost"
              size="icon"
              className="size-7"
              onClick={() => setZoom((z) => Math.min(2.2, z + 0.15))}
              title="Zoom in"
            >
              <ZoomIn className="size-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="size-7"
              onClick={() => setZoom((z) => Math.max(0.4, z - 0.15))}
              title="Zoom out"
            >
              <ZoomOut className="size-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="size-7"
              onClick={resetView}
              title="Reset view"
            >
              <RotateCcw className="size-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="size-7"
              onClick={fitToScreen}
              title="Fit to view"
            >
              <Maximize2 className="size-3.5" />
            </Button>
          </div>
        </div>
      </div>

      {/* Canvas Viewport */}
      <div
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        style={{ height }}
        className="relative w-full cursor-grab active:cursor-grabbing overflow-hidden bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-muted/20 via-background to-background"
      >
        <svg
          width={bounds.width}
          height={bounds.height}
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: "0 0",
            transition: isDragging ? "none" : "transform 0.1s ease-out",
          }}
          className="absolute inset-0 pointer-events-none"
        >
          <defs>
            <marker
              id="dag-arrow"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="6"
              markerHeight="6"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 9 5 L 0 9 z" fill="color-mix(in oklab, var(--border) 90%, black)" />
            </marker>
            <marker
              id="dag-arrow-active"
              viewBox="0 0 10 10"
              refX="8"
              refY="5"
              markerWidth="7"
              markerHeight="7"
              orient="auto-start-reverse"
            >
              <path d="M 0 1 L 9 5 L 0 9 z" fill="var(--accent-foreground)" />
            </marker>
          </defs>

          {/* Edges */}
          {positionedEdges.map((edge) => {
            if (!edge) return null;
            const isLit = highlighted.edges.has(edge.id);
            const dx = edge.x2 - edge.x1;
            const cx1 = edge.x1 + dx * 0.5;
            const cy1 = edge.y1;
            const cx2 = edge.x1 + dx * 0.5;
            const cy2 = edge.y2;
            const pathD = `M ${edge.x1} ${edge.y1} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${edge.x2} ${edge.y2}`;

            return (
              <path
                key={edge.id}
                d={pathD}
                fill="none"
                stroke={
                  isLit
                    ? "var(--accent-foreground)"
                    : "color-mix(in oklab, var(--border) 80%, transparent)"
                }
                strokeWidth={isLit ? 2.5 : 1.2}
                strokeDasharray={edge.type === "TESTED_BY" ? "4 3" : undefined}
                markerEnd={isLit ? "url(#dag-arrow-active)" : "url(#dag-arrow)"}
                className="transition-colors duration-200"
              />
            );
          })}
        </svg>

        {/* Nodes Layer */}
        <div
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: "0 0",
            width: bounds.width,
            height: bounds.height,
            position: "absolute",
            pointerEvents: "none",
          }}
        >
          {Object.entries(positionedNodes).map(([id, pos]) => {
            const isSelected = selectedId === id;
            const isHovered = hoveredId === id;
            const isHighlighted = highlighted.nodes.has(id);
            const isSearchMatch =
              search.trim() && pos.number.toLowerCase().includes(search.toLowerCase());

            return (
              <div
                key={id}
                style={{
                  position: "absolute",
                  left: pos.x,
                  top: pos.y,
                  width: pos.width,
                  height: pos.height,
                  pointerEvents: "auto",
                }}
                onMouseEnter={() => setHoveredId(id)}
                onMouseLeave={() => setHoveredId(null)}
                onClick={() => {
                  setSelectedId(id);
                  onSelectNode?.(id);
                }}
                className={`group flex cursor-pointer items-center justify-between rounded-xl border px-3 py-2 text-xs transition-all shadow-xs ${
                  isSelected
                    ? "border-accent-foreground bg-accent/35 ring-2 ring-accent-foreground shadow-md scale-105"
                    : isSearchMatch
                      ? "border-warning-foreground bg-warning/20 ring-2 ring-warning"
                      : isHighlighted
                        ? "border-accent-foreground/80 bg-accent/20"
                        : "border-border/80 bg-card hover:border-accent-foreground/50 hover:bg-background"
                }`}
              >
                <div className="min-w-0">
                  <p className="truncate font-mono font-bold text-primary">{pos.number}</p>
                  <p className="text-[9px] text-muted-foreground">Layer {pos.layer}</p>
                </div>
                <span className="size-2 rounded-full bg-accent-foreground/60 group-hover:bg-accent-foreground" />
              </div>
            );
          })}
        </div>

        {/* Inspector Panel Floating Overlay */}
        {selectedNode && (
          <aside className="absolute bottom-4 left-4 right-4 max-h-[calc(100%-2rem)] overflow-y-auto sm:bottom-auto sm:left-auto sm:right-4 sm:top-4 sm:w-80 rounded-xl border border-border/80 bg-card/95 p-4 shadow-xl backdrop-blur-md space-y-3">
            <div className="flex items-center justify-between border-b border-border/60 pb-2">
              <div className="flex items-center gap-1.5">
                <span className="eyebrow">Standard Inspector</span>
              </div>
              <Button
                asChild
                size="sm"
                variant="ghost"
                className="h-6 gap-1 px-1.5 text-xs text-accent-foreground"
              >
                <Link to="/standard/$id" params={{ id: selectedNode.id }}>
                  <span>Record</span>
                  <ExternalLink className="size-3" />
                </Link>
              </Button>
            </div>

            <div>
              <p className="font-mono text-base font-extrabold text-primary">
                {selectedNode.number}
              </p>
              <p className="text-xs text-muted-foreground">
                Layer {selectedNode.layer} in topological ordering
              </p>
            </div>

            {/* Direct Dependencies */}
            <div className="space-y-1.5 text-xs border-t border-border/60 pt-2">
              <div className="flex justify-between text-muted-foreground text-[11px] font-bold uppercase">
                <span>Normative Dependencies ({highlighted.up.length})</span>
              </div>
              {highlighted.up.length > 0 ? (
                <div className="flex flex-wrap gap-1">
                  {highlighted.up.map((num) => (
                    <span
                      key={num}
                      className="rounded bg-accent/20 px-2 py-0.5 font-mono text-[11px] font-semibold text-accent-foreground"
                    >
                      {num}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-[11px] text-muted-foreground">
                  Root standard (no prerequisites)
                </p>
              )}
            </div>

            {/* Required By */}
            <div className="space-y-1.5 text-xs border-t border-border/60 pt-2">
              <div className="flex justify-between text-muted-foreground text-[11px] font-bold uppercase">
                <span>Required By Standards ({highlighted.down.length})</span>
              </div>
              {highlighted.down.length > 0 ? (
                <div className="flex flex-wrap gap-1">
                  {highlighted.down.map((num) => (
                    <span
                      key={num}
                      className="rounded bg-muted px-2 py-0.5 font-mono text-[11px] font-semibold text-foreground"
                    >
                      {num}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-[11px] text-muted-foreground">Leaf standard</p>
              )}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}
