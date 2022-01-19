
import { Point } from "@ustutt/grapheditor-webcomponent/lib/edge";
import GraphEditor from "@ustutt/grapheditor-webcomponent/lib/grapheditor";
import { GroupBehaviour } from "@ustutt/grapheditor-webcomponent/lib/grouping";
import { Node } from "@ustutt/grapheditor-webcomponent/lib/node";
import { calculateBoundingRect, Rect } from "@ustutt/grapheditor-webcomponent/lib/util";
import { BOUNDING_BOX_PADDING } from "./node-templates";


export class TaxonomyGroupBehaviour implements GroupBehaviour {
    moveChildrenAlongGoup = true;
    captureDraggedNodes = false;
    allowFreePositioning = true;
    allowDraggedNodesLeavingGroup = false;

    afterNodeJoinedGroup(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor, atPosition?: Point) {
        this.repositionChildren(group, groupNode, graphEditor);
    }

    afterNodeLeftGroup(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor) {
        this.repositionChildren(group, groupNode, graphEditor);
    }

    repositionChildren(group: string, groupNode: Node, graphEditor: GraphEditor): void {
        if (groupNode == null) {
            return;
        }
        const childNodeWidth = 120;
        const childNodeHeight = 60;

        const taxonomyItemPadding = BOUNDING_BOX_PADDING * 4;

        const ellipseScale = 1.4;


        const childNodes: Node[] = [];
        graphEditor.groupingManager.getAllChildrenOf(group).forEach(childId => childNodes.push(graphEditor.getNode(childId)));
        childNodes.sort((a, b) => (a?.z ?? Infinity) - (b?.z ?? Infinity));

        if (childNodes.length === 0) {
            groupNode.width = null;
            groupNode.height = null;
            return; // fast exit let template handle min dimensions
        }

        const itemsPerColumn = Math.max(2, Math.round(Math.sqrt(childNodes.length / 2)));
        const columnNr = Math.max(1, Math.ceil(childNodes.length / itemsPerColumn));
        const rowNr = Math.max(1, Math.min(childNodes.length, itemsPerColumn));

        const width: number = (childNodeWidth * columnNr) + (taxonomyItemPadding * (columnNr - 1));
        const height: number = (childNodeHeight * rowNr) + (taxonomyItemPadding * (rowNr - 1));

        const startX = groupNode.x + (-width / 2) + (childNodeWidth / 2);
        const startY = groupNode.y + (-height / 2) + (childNodeHeight / 2);

        let row = 0;
        let column = 0;

        childNodes.forEach(childNode => {
            childNode.x = startX + (column * (childNodeWidth + taxonomyItemPadding));
            childNode.y = startY + (row * (childNodeHeight + taxonomyItemPadding));

            row++;
            if (row >= itemsPerColumn) {
                row = 0;
                column++;
            }

        });

        groupNode.width = width * ellipseScale;
        groupNode.height = height * ellipseScale;
    }

    calcSize(groupNode: Node, groupId: string, graphEditor: GraphEditor) {
        if (graphEditor.groupingManager.getAllChildrenOf(groupId).size > 1) {

            const itemsPerColumn = Math.max(2, Math.round(Math.sqrt(graphEditor.groupingManager.getAllChildrenOf(groupId).size / 2)));
            groupNode.height = 100 * itemsPerColumn;
            groupNode.childVisible = true;
            groupNode.width = (2 + graphEditor.groupingManager.getAllChildrenOf(groupId).size / itemsPerColumn) * (160);
        } else {
            groupNode.height = 20;
            groupNode.width = 140;
            groupNode.childVisible = false;
        }
    }

    onNodeMoveEnd(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor) { // TODO remove
    }

}

export class TypeGroupBehaviour implements GroupBehaviour {
    moveChildrenAlongGoup = true;
    captureDraggedNodes = false;
    allowFreePositioning = true;
    allowDraggedNodesLeavingGroup = false;

    afterNodeJoinedGroup(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor, atPosition?: Point): void {
        this.repositionChildren(group, groupNode, graphEditor);
    }

    afterNodeLeftGroup(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor): void {
        this.repositionChildren(group, groupNode, graphEditor);
    }

    repositionChildren(group: string, groupNode: Node, graphEditor: GraphEditor): void {
        if (groupNode == null) {
            return;
        }
        const childNodeWidth = 120;
        const childNodeHeight = 60;
        const extraTextPadding = 16;

        const x = groupNode.x;
        let startY = groupNode.y + extraTextPadding;

        const childNodes: Node[] = [];
        graphEditor.groupingManager.getAllChildrenOf(group).forEach(childId => childNodes.push(graphEditor.getNode(childId)));
        childNodes.sort((a, b) => (a?.z ?? Infinity) - (b?.z ?? Infinity));

        if (childNodes.length === 0) {
            groupNode.width = null;
            groupNode.height = null;
            return; // fast exit let template handle min dimensions
        }

        const count = childNodes.length;

        const width: number = childNodeWidth;
        const height: number = (childNodeHeight * count) + (BOUNDING_BOX_PADDING * count);

        startY -= height / 2;

        childNodes.forEach(child => {
            child.x = x;
            child.y = startY + (childNodeHeight / 2);

            // handle updates to pinned coordinates
            if (child.fx != null) {
                child.fx = child.x;
                child.fy = child.y;
            }

            // shift to next y
            startY += childNodeHeight + BOUNDING_BOX_PADDING;
        });

        groupNode.width = width;
        groupNode.height = height + extraTextPadding;
    }

    onNodeMoveEnd(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor): void {
        const children = graphEditor.groupingManager.getAllChildrenOf(group);

        const boxes: Rect[] = [];
        children.forEach(childId => {
            const node = graphEditor.getNode(childId);
            const bbox = graphEditor.getNodeBBox(childId);
            boxes.push({
                x: node.x + bbox.x,
                y: node.y + bbox.y,
                width: bbox.width,
                height: bbox.height,
            });
        });

        const minBox = calculateBoundingRect(...boxes);

        groupNode.width = minBox.width;
        groupNode.height = minBox.height + 10 + BOUNDING_BOX_PADDING; // + 10 for title text

        const dx = (minBox.x + (minBox.width / 2)) - groupNode.x;
        const dy = (minBox.y - 10 + (minBox.height / 2)) - groupNode.y;

        groupNode.x = groupNode.x + dx;
        groupNode.y = groupNode.y + dy;

        graphEditor.moveNode(groupNode.id, groupNode.x, groupNode.y, false);

        graphEditor.completeRender();
    }
}

