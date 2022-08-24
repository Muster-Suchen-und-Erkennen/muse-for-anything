import { Edge, edgeId } from "@ustutt/grapheditor-webcomponent/lib/edge";
import GraphEditor from "@ustutt/grapheditor-webcomponent/lib/grapheditor";
import { Node } from "@ustutt/grapheditor-webcomponent/lib/node";
import { forceCenter, forceCollide, forceLink, forceManyBody, forceSimulation, forceX, forceY } from "d3-force";
import createLayout from "ngraph.forcelayout";
import createGraph from "ngraph.graph";


/**
 * calculate the nodes position based on the ngraph.forcedirected algorithm
 * store the positions in each node
 */
export function calculateNodePositionsNgraph(graph: GraphEditor, distanceBetweenElements: number) {
    const gm = graph.groupingManager;
    const g = createGraph<string, unknown>();

    const nodes = graph.nodeList.filter(node => node.type === "type-node" || node.type === "taxonomy-node");
    const nodesMap = new Map<string, string>();
    nodes.forEach(node => {
        g.addNode(node.id);
        const nodeId = node.id.toString();
        nodesMap.set(nodeId, nodeId);
        gm.getAllChildrenOf(nodeId).forEach(child => {
            nodesMap.set(child, nodeId);
        });
    });
    graph.edgeList.forEach(edge => {
        let source = edge.source.toString();
        const target = edge.target.toString();
        if (edge.sourceRoot != null) {
            source = edge.sourceRoot;
        }
        if (nodesMap.has(source) && nodesMap.has(target)) {
            g.addLink(nodesMap.get(source), nodesMap.get(target));
        }
    });

    const physicsSettings = {
        timeStep: 0.5,
        dimensions: 2,
        gravity: -12 * ((((distanceBetweenElements / 100) - 1) / 3) + 1),
        theta: 0.8,
        springLength: 500 * (distanceBetweenElements / 100),
        springCoefficient: 0.8,
        dragCoefficient: 0.9,
    };

    const layout = createLayout(g, physicsSettings);

    nodes.forEach(node => {
        // set current positions and pin nodes
        layout.setNodePosition(node.id, node.x, node.y);
        if (node.fx != null && node.fy != null) {
            layout.pinNode(g.getNode(node.id), true);
        }
    });
    for (let i = 0; i < 500; ++i) {
        layout.step();
    }

    g.forEachNode(node => {
        const pos = layout.getNodePosition(node.id);
        graph.moveNode(node.id, pos.x, pos.y, false);
    });
    graph.updateGraphPositions();
}

/**
 * calculate the nodes position based on the d3-force algorithm
 * store the positions in each node
 */
export function calculateNodePositionsd3(graph: GraphEditor, distanceBetweenElements: number) {
    const gm = graph.groupingManager;

    const nodes: Node[] = graph.nodeList.filter(node => node.type === "type-node" || node.type === "taxonomy-node").map(node => {
        const n: Node = {
            id: node.id,
            x: isNaN(node.x) ? 0 : node.x,
            y: isNaN(node.y) ? 0 : node.y,
        };
        if (node.fx != null) {
            n.fx = node.fx;
        }
        if (node.fy != null) {
            n.fy = node.fy;
        }
        if (node.width != null) {
            n.width = node.width;
        }
        if (node.height != null) {
            n.height = node.height;
        }
        return n;
    });
    const links: Edge[] = [];

    const nodesMap = new Map<string, Node>();
    nodes.forEach(node => {
        const nodeId = node.id.toString();
        nodesMap.set(nodeId, node);
        gm.getAllChildrenOf(nodeId).forEach(child => {
            nodesMap.set(child, node);
        });
    });
    graph.edgeList.forEach(edge => {
        let source = edge.source.toString();
        const target = edge.target.toString();
        if (edge.sourceRoot != null) {
            source = edge.sourceRoot;
        }
        if (nodesMap.has(source) && nodesMap.has(target)) {
            const sourceNode = nodesMap.get(source);
            const targetNode = nodesMap.get(target);
            const link = {
                id: edgeId(edge),
                source: sourceNode.id.toString(),
                target: targetNode.id.toString(),
                sourceNode,
                targetNode,
            };
            links.push(link);
        }
    });

    forceSimulation(nodes)
        .force("center", forceCenter(0, 0))
        .force(
            "link",
            forceLink(links)
                .id(d => d.id)
                .distance(d => {
                    // factor in node radius into link length as length is counted from the node center
                    const sourceRadius = calcRadius(d.sourceNode);
                    const targetRadius = calcRadius(d.targetNode);
                    return Math.max(30, (((distanceBetweenElements - 100) * 1.5) + 100) + sourceRadius + targetRadius);
                }),
        )
        .force(
            "charge",
            forceManyBody()
                .strength(d => Math.min(-1, -calcRadius(d) * Math.max(0.3, 1.1 * (distanceBetweenElements / 100))))
                .distanceMin(2)
                .distanceMax(1000),
        )
        .force(
            "collision",
            forceCollide()
                .radius(d => calcRadius(d))
                .strength(0.8),
        )
        .force("centralGravityX", forceX(0).strength(0.01))
        .force("centralGravityY", forceY(0).strength(0.01))
        .stop()
        .tick(300);


    nodes.forEach(node => {
        graph.moveNode(node.id, node.x, node.y, false);
    });
    graph.updateGraphPositions();

}


/**
 * calculate the radius for a given node for a good layouting with d3-force
 * @param d node of the graph
 * @returns radius of the given node
 */
function calcRadius(d: Node) {
    let width = d.width ?? 0;
    let height = d.height ?? 0;
    if (isNaN(width)) {
        width = 0;
    }
    if (isNaN(height)) {
        height = 0;
    }
    const radius = Math.max(60, width / 2, height / 2);
    return radius;
}
