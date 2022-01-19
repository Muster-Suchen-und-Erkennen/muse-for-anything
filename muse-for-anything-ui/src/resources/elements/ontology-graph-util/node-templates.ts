import { DynamicNodeTemplate, DynamicTemplateContext } from "@ustutt/grapheditor-webcomponent/lib/dynamic-templates/dynamic-template";
import GraphEditor from "@ustutt/grapheditor-webcomponent/lib/grapheditor";
import { LinkHandle } from "@ustutt/grapheditor-webcomponent/lib/link-handle";
import { Node } from "@ustutt/grapheditor-webcomponent/lib/node";

export const BOUNDING_BOX_PADDING: number = 10;


export class TypeNodeTemplate implements DynamicNodeTemplate {

    static MIN_WIDTH = 120;
    static MIN_HEIGHT = 20;

    getLinkHandles(g: any, grapheditor: GraphEditor): LinkHandle[] {
        const node: Node = g.datum();
        const nodeWidth = isNaN(node.width ?? TypeNodeTemplate.MIN_WIDTH) ? TypeNodeTemplate.MIN_WIDTH : node.width ?? TypeNodeTemplate.MIN_WIDTH;
        const nodeHeight = isNaN(node.height ?? TypeNodeTemplate.MIN_HEIGHT) ? TypeNodeTemplate.MIN_HEIGHT : node.height ?? TypeNodeTemplate.MIN_HEIGHT;
        const width = nodeWidth + 2 * BOUNDING_BOX_PADDING;
        const height = nodeHeight + 2 * BOUNDING_BOX_PADDING;
        const handles = [
            {
                id: 0,
                normal: { dx: 1, dy: 0 },
                x: width / 2,
                y: 0,
            },
            {
                id: 1,
                normal: { dx: 0, dy: 1 },
                x: 0,
                y: height / 2,
            },
            {
                id: 2,
                normal: { dx: -1, dy: 0 },
                x: -width / 2,
                y: 0,
            },
            {
                id: 3,
                normal: { dx: 0, dy: -1 },
                x: 0,
                y: -height / 2,
            },
        ];

        return handles;
    }

    renderInitialTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        const isOverviewGraph = grapheditor.className.includes("graphoverview");
        const width = TypeNodeTemplate.MIN_WIDTH + (BOUNDING_BOX_PADDING * 2);
        const height = TypeNodeTemplate.MIN_HEIGHT + (BOUNDING_BOX_PADDING * 2);
        const x = -width / 2;
        const y = -height / 2;
        g.append("rect")
            .classed("type-group", true)
            .attr("x", x)
            .attr("y", y)
            .attr("width", width)
            .attr("height", height)
            .attr("rx", 5);
        if (!isOverviewGraph) {
            g.append("text")
                .attr("x", x + BOUNDING_BOX_PADDING)
                .attr("y", y + BOUNDING_BOX_PADDING + 10)
                .classed("title", true)
                .attr("data-click", "header")
                .attr("width", TypeNodeTemplate.MIN_WIDTH)
                .attr("data-content", "title");
            g.append("title")
                .attr("data-content", "title");
        }
    }

    updateTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        const node = g.datum();
        let baseWidth = node.width;
        let baseHeight = node.height;
        if (isNaN(baseWidth) || baseWidth == null || baseWidth < TypeNodeTemplate.MIN_WIDTH) {
            baseWidth = TypeNodeTemplate.MIN_WIDTH;
        }
        if (isNaN(baseHeight) || baseHeight == null || baseHeight < TypeNodeTemplate.MIN_HEIGHT) {
            baseHeight = TypeNodeTemplate.MIN_HEIGHT;
        }
        const width = baseWidth + BOUNDING_BOX_PADDING * 2;
        const height = baseHeight + BOUNDING_BOX_PADDING * 2;
        const x = -width / 2;
        const y = -height / 2;

        g.select("rect.type-group")
            .attr("x", x)
            .attr("y", y)
            .attr("width", width)
            .attr("height", height);
        g.select("text.title")
            .attr("x", x + BOUNDING_BOX_PADDING)
            .attr("y", y + BOUNDING_BOX_PADDING + 10)
            .attr("width", baseWidth)
            .attr("data-wrapped", null); // reset text wrapping // FIXME remove after grapheditor upgrade
    }
}

export class TaxonomyNodeTemplate implements DynamicNodeTemplate {

    static MIN_WIDTH = 140;
    static MIN_HEIGHT = 20;

    getLinkHandles(g: any, grapheditor: GraphEditor): LinkHandle[] {
        const node: Node = g.datum();
        const nodeWidth = isNaN(node.width ?? TypeNodeTemplate.MIN_WIDTH) ? TypeNodeTemplate.MIN_WIDTH : node.width ?? TypeNodeTemplate.MIN_WIDTH;
        const nodeHeight = isNaN(node.height ?? TypeNodeTemplate.MIN_HEIGHT) ? TypeNodeTemplate.MIN_HEIGHT : node.height ?? TypeNodeTemplate.MIN_HEIGHT;
        const width = nodeWidth + 2 * BOUNDING_BOX_PADDING;
        const height = nodeHeight + 2 * BOUNDING_BOX_PADDING;
        const handles = [
            {
                id: 0,
                normal: { dx: 1, dy: 0 },
                x: width / 2,
                y: 0,
            },
            {
                id: 1,
                normal: { dx: 0, dy: 1 },
                x: 0,
                y: height / 2,
            },
            {
                id: 2,
                normal: { dx: -1, dy: 0 },
                x: -width / 2,
                y: 0,
            },
            {
                id: 3,
                normal: { dx: 0, dy: -1 },
                x: 0,
                y: -height / 2,
            },
        ];

        return handles;
    }

    renderInitialTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        const isOverviewGraph = grapheditor.className.includes("graphoverview");
        const width = TaxonomyNodeTemplate.MIN_WIDTH + (BOUNDING_BOX_PADDING * 2);
        const height = TaxonomyNodeTemplate.MIN_HEIGHT + (BOUNDING_BOX_PADDING * 2);
        g.append("ellipse")
            .classed("taxonomy-group", true)
            .attr("cx", 0)
            .attr("cy", 0)
            .attr("rx", width / 2)
            .attr("ry", height / 2);
        if (!isOverviewGraph) {
            g.append("text")
                .attr("x", (-width / 2) + BOUNDING_BOX_PADDING)
                .attr("y", 0)
                .classed("title", true)
                .attr("data-click", "header")
                .attr("data-text-center-y", 0)
                .attr("width", TaxonomyNodeTemplate.MIN_WIDTH)
                .attr("data-content", "title");
            g.append("title")
                .attr("data-content", "title");
        }
    }

    updateTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        const node = g.datum();
        let baseWidth = node.width;
        let baseHeight = node.height;
        if (isNaN(baseWidth) || baseWidth == null || baseWidth < TypeNodeTemplate.MIN_WIDTH) {
            baseWidth = TypeNodeTemplate.MIN_WIDTH;
        }
        if (isNaN(baseHeight) || baseHeight == null || baseHeight < TypeNodeTemplate.MIN_HEIGHT) {
            baseHeight = TypeNodeTemplate.MIN_HEIGHT;
        }
        const width = baseWidth + BOUNDING_BOX_PADDING * 2;
        const height = baseHeight + BOUNDING_BOX_PADDING * 2;

        g.select("ellipse.taxonomy-group")
            .attr("rx", width / 2)
            .attr("ry", height / 2);

        g.select("text.title")
            .attr("x", (-width / 2) + BOUNDING_BOX_PADDING);
    }

    private calculateRect(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>, updated?: boolean) {
        const isOverviewGraph = grapheditor.className.includes("graphoverview");
        const props = g.datum();
        if (!props.height) {
            props.height = 20;
        }
        if (!props.width) {
            props.width = 140;
        }
        if (!props.childVisible) {
            props.childVisible = false;
        }
        this.drawRect(g, { x: 0, y: 0, width: props.width, height: props.height }, props, props.childVisible, isOverviewGraph);
    }

    private drawRect(g: any, minBox: any, props: any, childsVisible: boolean, isOverviewGraph: boolean) {
        g.selectAll("*").remove();
        g.append("ellipse")
            .attr("width", minBox.width + BOUNDING_BOX_PADDING * 2)
            .attr("height", minBox.height + BOUNDING_BOX_PADDING * 2)
            .attr("cx", (minBox.width + BOUNDING_BOX_PADDING * 2) / 2)
            .attr("cy", (minBox.height + BOUNDING_BOX_PADDING * 2) / 2)
            .attr("rx", (minBox.width + BOUNDING_BOX_PADDING * 2) / 2)
            .attr("ry", (minBox.height + BOUNDING_BOX_PADDING * 2) / 2)
            .attr("class", "taxonomy-group");
        if (!isOverviewGraph) {
            g.append("text")
                .attr("x", 15)
                .attr("y", (minBox.height + BOUNDING_BOX_PADDING * 2) / 2 + 5)
                .attr("class", "title")
                .attr("width", 150)
                .attr("data-click", "header")
                .attr("data-content", "title");
            g.append("title")
                .attr("data-content", "title");

            // add + or - to node for collapsing details or not
            const collapseIconElement = g.append("g")
                .attr("transform", `translate(${minBox.width / 2},5)`)
                .attr("data-click", "expandNode")
                .attr("fill", "white")
                .attr("fill-rule", "evenodd")
                .attr("stroke", "currentColor")
                .attr("stroke-linecap", "round")
                .attr("stroke-linejoin", "round");
            collapseIconElement.append("path").attr("d", "m12.5 10.5v-8c0-1.1045695-.8954305-2-2-2h-8c-1.1045695 0-2 .8954305-2 2v8c0 1.1045695.8954305 2 2 2h8c1.1045695 0 2-.8954305 2-2z");
            collapseIconElement.append("path").attr("d", "m6.5 3.5v6")
                .attr("transform", "matrix(0 1 -1 0 13 0)");

            if (!childsVisible) {
                collapseIconElement.append("path").attr("d", "m6.5 3.5v6.056");
            }
        }
    }
}

export class OverviewGraphNode implements DynamicNodeTemplate {

    getLinkHandles(g: any, grapheditor: GraphEditor): LinkHandle[] {
        return;
    }

    renderInitialTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        const props = g.datum();
        this.drawRect(g, props);
    }

    updateTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        const props = g.datum();
        g.selectAll("rect")
            .attr("width", props.width)
            .attr("height", props.height);
    }

    private drawRect(g: any, props: any) {
        g.selectAll("*").remove();
        g.append("rect")
            .attr("width", props.width)
            .attr("height", props.height)
            .attr("x", 0)
            .attr("y", 0)
            .attr("class", props.class)
            .attr("rx", 0);
    }
}
