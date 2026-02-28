import { useState, useEffect, useRef, useCallback } from 'react'
import { Network } from 'vis-network'
import { DataSet } from 'vis-data'
import axios from 'axios'

interface GraphNode {
  id: string
  label: string
  name: string
  dynasty?: string
  role?: string
}

interface GraphEdge {
  source: string
  target: string
  type: string
}

const API_BASE = '/api'

function App() {
  const [nodes, setNodes] = useState<GraphNode[]>([])
  const [edges, setEdges] = useState<GraphEdge[]>([])
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<GraphNode[]>([])
  const networkRef = useRef<HTMLDivElement>(null)
  const networkInstanceRef = useRef<Network | null>(null)

  // Load graph data
  useEffect(() => {
    const fetchGraph = async () => {
      try {
        setLoading(true)
        const response = await axios.get(`${API_BASE}/graph`)
        setNodes(response.data.nodes)
        setEdges(response.data.edges)
        setError(null)
      } catch (err) {
        setError('Failed to load graph data. Make sure the backend is running.')
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchGraph()
  }, [])

  // Initialize network
  useEffect(() => {
    if (!networkRef.current || nodes.length === 0) return

    const nodeDataSet = new DataSet(
      nodes.map((n) => ({
        id: n.id,
        label: n.name,
        group: n.label,
        title: `${n.name}\n${n.label}${n.dynasty ? ` - ${n.dynasty}` : ''}`,
      }))
    )

    const edgeDataSet = new DataSet(
      edges.map((e, i) => ({
        id: i,
        from: e.source,
        to: e.target,
        label: e.type,
        arrows: 'to',
      }))
    )

    const options = {
      nodes: {
        shape: 'dot',
        size: 16,
        font: {
          size: 14,
          color: '#333',
        },
        borderWidth: 2,
        color: {
          background: '#667eea',
          border: '#5568d3',
          highlight: {
            background: '#764ba2',
            border: '#6a4090',
          },
        },
      },
      edges: {
        width: 1,
        color: { color: '#999', highlight: '#667eea' },
        smooth: {
          type: 'continuous',
        },
      },
      physics: {
        stabilization: false,
        barnesHut: {
          gravitationalConstant: -2000,
          springConstant: 0.04,
          springLength: 150,
        },
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
      },
    }

    networkInstanceRef.current = new Network(networkRef.current, { nodes: nodeDataSet, edges: edgeDataSet }, options)

    networkInstanceRef.current.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0]
        const node = nodes.find((n) => n.id === nodeId)
        if (node) {
          setSelectedNode(node)
        }
      }
    })

    return () => {
      networkInstanceRef.current?.destroy()
    }
  }, [nodes, edges])

  // Handle search
  const handleSearch = useCallback(async (query: string) => {
    setSearchQuery(query)
    if (!query.trim()) {
      setSearchResults([])
      return
    }

    try {
      const response = await axios.get(`${API_BASE}/search?q=${encodeURIComponent(query)}`)
      setSearchResults(response.data.results)
    } catch (err) {
      console.error('Search failed:', err)
    }
  }, [])

  // Highlight node on click in sidebar
  const handleResultClick = (node: GraphNode) => {
    setSelectedNode(node)
    networkInstanceRef.current?.selectNodes([node.id])
    networkInstanceRef.current?.focus(node.id, { scale: 1.2, animation: true })
  }

  return (
    <div className="app">
      <header className="header">
        <h1>中国人物画知识图谱</h1>
        <p>KGCFP - Chinese Figure Painting Knowledge Graph</p>
      </header>

      <div className="main-content">
        <div className="graph-container">
          <div id="network" ref={networkRef}></div>
          {loading && (
            <div className="loading">
              <p>Loading knowledge graph...</p>
            </div>
          )}
          {error && <div className="error">{error}</div>}
        </div>

        <aside className="sidebar">
          <div className="sidebar-header">
            <input
              type="text"
              className="search-input"
              placeholder="搜索人物、作品..."
              value={searchQuery}
              onChange={(e) => handleSearch(e.target.value)}
            />
          </div>

          <div className="sidebar-content">
            {selectedNode && (
              <div className="node-card" style={{ cursor: 'default' }}>
                <span className="label">{selectedNode.label}</span>
                <h4>{selectedNode.name}</h4>
                {selectedNode.dynasty && <p className="dynasty">{selectedNode.dynasty}</p>}
                {selectedNode.role && <p className="dynasty">Role: {selectedNode.role}</p>}
              </div>
            )}

            {searchResults.length > 0 && (
              <>
                <h3 style={{ marginBottom: '0.75rem', fontSize: '0.9rem', color: '#666' }}>
                  Search Results ({searchResults.length})
                </h3>
                {searchResults.map((node) => (
                  <div
                    key={node.id}
                    className="node-card"
                    onClick={() => handleResultClick(node)}
                  >
                    <span className="label">{node.label}</span>
                    <h4>{node.name}</h4>
                    {node.dynasty && <p className="dynasty">{node.dynasty}</p>}
                  </div>
                ))}
              </>
            )}

            {searchResults.length === 0 && !selectedNode && !loading && (
              <div style={{ color: '#999', textAlign: 'center', padding: '2rem' }}>
                <p>Enter a search term to find nodes</p>
                <p style={{ marginTop: '0.5rem', fontSize: '0.85rem' }}>
                  Click on a node in the graph to view details
                </p>
              </div>
            )}
          </div>
        </aside>
      </div>
    </div>
  )
}

export default App
