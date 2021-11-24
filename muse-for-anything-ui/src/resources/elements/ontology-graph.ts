import { bindable, autoinject, observable, child } from "aurelia-framework";
import { BindingEngine } from 'aurelia-framework';
import { EventAggregator, Subscription } from "aurelia-event-aggregator";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiObject } from "rest/api-objects";
import { NavigationLinksService, NavLinks } from "services/navigation-links";
import { NAV_LINKS_CHANNEL } from "resources/events";
import GraphEditor from "@ustutt/grapheditor-webcomponent/lib/grapheditor";
import { Node } from "@ustutt/grapheditor-webcomponent/lib/node";
import { Point } from "@ustutt/grapheditor-webcomponent/lib/edge";
import { TaxonomyApiObject, TaxonomyItemApiObject, TaxonomyItemRelationApiObject } from "./taxonomy-graph";
import { GroupBehaviour } from "@ustutt/grapheditor-webcomponent/lib/grouping";
import { DynamicNodeTemplate, DynamicTemplateContext } from "@ustutt/grapheditor-webcomponent/lib/dynamic-templates/dynamic-template";
import { LinkHandle } from "@ustutt/grapheditor-webcomponent/lib/link-handle";
import { calculateBoundingRect, Rect } from "@ustutt/grapheditor-webcomponent/lib/util";
import * as fs from 'fs';
import { forceSimulation, forceLink, forceCenter, forceManyBody, forceCollide } from "d3-force";

const boundingBoxBorder: number = 20;
const smallMarkerSize: number = 0.8;
const largeMarkerSize: number = 1.8;

interface TypeApiObject extends ApiObject {
    collectionSize: number;
    items: ApiLink[];
    page: number;
}

interface TypeItemApiObject extends ApiObject {
    abstract: boolean;
    createdOn: string;
    deletedOn: string | null;
    name: string;
    description: string | null;
    version: number | null;
    schema: {
        abstract: boolean;
        definitions: {
            root: {
                properties: [any] | null,
                propertyOrder: [{
                    [prop: string]: number,
                }],
                titel: string | null,
                type: [any]

            } | null
        },
        description: string | null;
        titel: string;
    };
}

enum DataItemTypeEnum {
    TaxonomyItem = "taxonomyItem",
    TaxonomyItemProperty = "taxonomyItemProperty",
    TaxonomyProperty = "taxonomy",
    TypeItem = "typeItem",
    TypeProperty = "type",
    StringProperty = "string",
    NumberProperty = "number",
    IntegerProperty = "integer",
    EnumProperty = "enum",
    BooleanProperty = "boolean",
    Undefined = "undefined"
}

export class DataItemModel {
    public id: string;
    public name: string;
    public href: string;
    public description: string;
    public itemType: DataItemTypeEnum;
    public node: Node;
    public taxonomyParentRelations: string[];
    public position: { x, y }

    public icon: string;
    public children: DataItemModel[];
    public expanded: boolean;
    public visible: boolean;
    public abstract: boolean;
    @observable() isSelected: boolean;
    @observable() isVisibleInGraph: boolean;
    @observable() isSearchResult: boolean;
    @observable() childIsInResult: boolean;
    @observable() positionIsFixed: boolean;
    private graph: GraphEditor;


    constructor(id: string, name: string, abstract: boolean, href: string, description: string, itemType: DataItemTypeEnum, graph: GraphEditor, isVisible = true, taxonomyChildRelations = []) {
        this.id = id;
        this.name = name;
        this.abstract = abstract;
        this.href = href;
        this.description = description;
        this.itemType = itemType;
        this.expanded = false;
        this.visible = isVisible;
        this.graph = graph;
        this.children = [];
        this.taxonomyParentRelations = taxonomyChildRelations;
        this.isVisibleInGraph = true;
        this.positionIsFixed = false;
        this.childIsInResult = false;
    }

    hasChildren() {
        if (this.itemType == DataItemTypeEnum.TypeItem || this.itemType == DataItemTypeEnum.TaxonomyItem) {
            return true;
        }
        if(this.children.length>0){
            return true;
        }
        return false;
    }

    toggleNode() {
        for (var i = 0; i < this.children.length; i++) {
            this.children[i].visible = !this.children[i].visible;
            if (this.expanded) {
                this.children[i].toggleNode();
            }
        }
        this.expanded = !this.expanded;
        if (this.expanded === true) {
            this.icon = "arrow-down";
        } else {
            this.icon = "arrow-right";
        }
    }

    togglePositionFixed() {
        this.positionIsFixed = !this.positionIsFixed;
    }

    isSelectedChanged(newValue, oldValue) {
        if (newValue === true) {
            this.graph.selectNode(this.id);
        } else {
            this.graph.deselectNode(this.id);
        }
        this.graph.updateHighlights();

    }

    addChild(id: string, name: string, abstract: boolean, href: string, description: string, itemType: DataItemTypeEnum, childHrefs?: string[]) {
        this.children.push(new DataItemModel(id, name, abstract, href, description, itemType, this.graph, false, childHrefs));
        this.icon = "arrow-right";
        this.expanded = false;
    }

    addChildItem(item: DataItemModel) {
        this.children.push(item)
        this.icon = "arrow-right";
        this.expanded = false;
    }

    getLink() {
        if (this.itemType == DataItemTypeEnum.TypeItem) {
            let namespaceID = this.href.split("namespaces/")[1].split("/")[0]
            let typeID = this.href.split("types/")[1].split("/")[0]

            return "http://localhost:5000/explore/ont-namespace/:" + namespaceID + "/ont-type/:" + typeID
        } else if (this.itemType == DataItemTypeEnum.TaxonomyItem) {
            let namespaceID = this.href.split("namespaces/")[1].split("/")[0]
            let typeID = this.href.split("taxonomies/")[1].split("/")[0]

            return "http://localhost:5000/explore/ont-namespace/:" + namespaceID + "/ont-taxonomy/:" + typeID
        }
    }
}

class TypeNodeTemplate implements DynamicNodeTemplate {

    getLinkHandles(g: any, grapheditor: GraphEditor): LinkHandle[] {
        const width = g.datum().width + 2 * boundingBoxBorder;
        const height = g.datum().height + 2 * boundingBoxBorder;
        let handles = [];
        handles.push({
            id: 0,
            normal: { dx: 1, dy: 0 },
            x: width,
            y: height / 2
        });
        handles.push({
            id: 1,
            normal: { dx: -1, dy: 0 },
            x: 0,
            y: height / 2
        });
        handles.push({
            id: 2,
            normal: { dx: 0, dy: 1 },
            x: width / 2,
            y: height
        });
        handles.push({
            id: 3,
            normal: { dx: 0, dy: -1 },
            x: width / 2,
            y: 0
        });

        return handles;
    }

    renderInitialTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        this.calculateRect(g, grapheditor, context, false);
    }

    updateTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        let width = g.datum().width;
        let height = g.datum().height;
        if (height) {
            width += boundingBoxBorder * 2
            height += boundingBoxBorder * 2
        } else {
            width = 120;
            height = 30;
        }

        g.selectAll("rect").attr("width", width)
                            .attr("height", height)
        g.selectAll("text").attr("width", width - 5)
        g.selectAll("title").attr("width", width - 5)
    }

    private calculateRect(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>, updated?: boolean) {
        let isOverviewGraph = grapheditor.className.includes("graphoverview")
        const width = g.datum().width;
        const height = g.datum().height;
        if (height) {
            this.drawRect(g, { x: 0, y: 0, width: width, height: height }, g.datum(), isOverviewGraph)
        } else {
            this.drawRect(g, { x: 0, y: 0, width: 120, height: 20 }, g.datum(), isOverviewGraph)
        }
    }

    private drawRect(g: any, minBox: any, props: any, isOverviewGraph: boolean) {
        g.selectAll("*").remove();
        g.append("rect")
            .attr("width", minBox.width + boundingBoxBorder * 2)
            .attr("height", minBox.height + boundingBoxBorder * 2)
            .attr("class", "type-group")
            .attr("rx", 5);
        if (!isOverviewGraph) {
            g.append("text")
                .attr("x", 10)
                .attr("y", 20)
                .attr("class", "title")
                .attr("data-click", "header")
                .attr("width", minBox.width + boundingBoxBorder * 2 - 5)
                .attr('data-content', 'title');
            g.append("title")
                .attr('data-content', 'title')
                .attr("width", minBox.width + boundingBoxBorder * 2 - 5);
        }
    }
}

class TaxonomyNodeTemplate implements DynamicNodeTemplate {
    getLinkHandles(g: any, grapheditor: GraphEditor): LinkHandle[] {
        const width = g.datum().width + 2 * boundingBoxBorder;
        const height = g.datum().height + 2 * boundingBoxBorder;
        let handles = [];
        handles.push({
            id: 0,
            normal: { dx: 1, dy: 0 },
            x: width,
            y: height / 2
        });
        handles.push({
            id: 1,
            normal: { dx: -1, dy: 0 },
            x: 0,
            y: height / 2
        });
        handles.push({
            id: 2,
            normal: { dx: 0, dy: 1 },
            x: width / 2,
            y: height
        });
        handles.push({
            id: 3,
            normal: { dx: 0, dy: -1 },
            x: width / 2,
            y: 0
        });

        return handles;
    }

    renderInitialTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        this.calculateRect(g, grapheditor, context, false);
    }

    updateTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        let props = g.datum();
        if (!props.height) {
            props.height = 20;
        }
        if (!props.width) {
            props.width = 140;
        }

        g.selectAll("ellipse").attr("width", props.width + boundingBoxBorder * 2)
            .attr("height", props.height + boundingBoxBorder * 2)
            .attr("cx", (props.width + boundingBoxBorder * 2) / 2)
            .attr("cy", (props.height + boundingBoxBorder * 2) / 2)
            .attr("rx", (props.width + boundingBoxBorder * 2) / 2)
            .attr("ry", (props.height + boundingBoxBorder * 2) / 2)
        g.selectAll("text")
            .attr("y", (props.height + boundingBoxBorder * 2) / 2 + 5)
        g.selectAll("g")
            .attr("transform", "translate(" + props.width / 2 + ",5)")
    }

    private calculateRect(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>, updated?: boolean) {
        let isOverviewGraph = grapheditor.className.includes("graphoverview")
        let props = g.datum();
        if (!props.height) {
            props.height = 20;
        }
        if (!props.width) {
            props.width = 140;
        }
        if (!props.childVisible) {
            props.childVisible = false;
        }
        this.drawRect(g, { x: 0, y: 0, width: props.width, height: props.height }, props, props.childVisible, isOverviewGraph)
    }

    private drawRect(g: any, minBox: any, props: any, childsVisible: boolean, isOverviewGraph: boolean) {
        g.selectAll("*").remove();
        g.append("ellipse")
            .attr("width", minBox.width + boundingBoxBorder * 2)
            .attr("height", minBox.height + boundingBoxBorder * 2)
            .attr("cx", (minBox.width + boundingBoxBorder * 2) / 2)
            .attr("cy", (minBox.height + boundingBoxBorder * 2) / 2)
            .attr("rx", (minBox.width + boundingBoxBorder * 2) / 2)
            .attr("ry", (minBox.height + boundingBoxBorder * 2) / 2)
            .attr("class", "taxonomy-group")
        if (!isOverviewGraph) {
            g.append("text")
                .attr("x", 15)
                .attr("y", (minBox.height + boundingBoxBorder * 2) / 2 + 5)
                .attr("class", "title")
                .attr("width", 150)
                .attr("data-click", "header")
                .attr('data-content', 'title');
            g.append("title")
                .attr('data-content', 'title');

            // add + or - to node for collapsing details or not
            let collapseIconElement = g.append("g")
                .attr("transform", "translate(" + minBox.width / 2 + ",5)")
                .attr("data-click", "expandNode").attr("fill", "white").attr("fill-rule", "evenodd").attr("stroke", "currentColor").attr("stroke-linecap", "round").attr("stroke-linejoin", "round")
            collapseIconElement.append("path").attr("d", "m12.5 10.5v-8c0-1.1045695-.8954305-2-2-2h-8c-1.1045695 0-2 .8954305-2 2v8c0 1.1045695.8954305 2 2 2h8c1.1045695 0 2-.8954305 2-2z")
            collapseIconElement.append("path").attr("d", "m6.5 3.5v6").attr("transform", "matrix(0 1 -1 0 13 0)")

            if (!childsVisible) collapseIconElement.append("path").attr("d", "m6.5 3.5v6.056")
        }
    }
}

class OverviewGraphNode implements DynamicNodeTemplate {

    getLinkHandles(g: any, grapheditor: GraphEditor): LinkHandle[] {
        return;
    }

    renderInitialTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        let props = g.datum();
        this.drawRect(g, props);
    }

    updateTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        let props = g.datum();
        g.selectAll("rect")
            .attr("width", props.width)
            .attr("height", props.height)
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

class TaxonomyGroupBehaviour implements GroupBehaviour {
    moveChildrenAlongGoup = true;
    captureDraggedNodes = false;
    allowFreePositioning = true;
    allowDraggedNodesLeavingGroup = false;

    afterNodeJoinedGroup(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor, atPosition?: Point) {
        this.calcSize(groupNode, group, graphEditor);
    }

    afterNodeLeftGroup(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor) {
        this.calcSize(groupNode, group, graphEditor);
    }

    calcSize(groupNode: Node, groupId: string, graphEditor: GraphEditor) {
        if (graphEditor.groupingManager.getAllChildrenOf(groupId).size > 1) {

            let itemsPerColumn = Math.max(2, Math.round(Math.sqrt(graphEditor.groupingManager.getAllChildrenOf(groupId).size / 2)))
            groupNode.height = 100 * itemsPerColumn;
            groupNode.childVisible = true;
            groupNode.width = (2 + graphEditor.groupingManager.getAllChildrenOf(groupId).size / itemsPerColumn) * (160)
        } else {
            groupNode.height = 20;
            groupNode.width = 140;
            groupNode.childVisible = false;
        }
    }

    onNodeMoveEnd(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor) {
    }

}

class TypeGroupBehaviour implements GroupBehaviour {
    moveChildrenAlongGoup = true;
    captureDraggedNodes = false;
    allowFreePositioning = true;
    allowDraggedNodesLeavingGroup = false;

    afterNodeJoinedGroup(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor, atPosition?: Point) {
        this.calcSize(groupNode, group, graphEditor);
    }

    afterNodeLeftGroup(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor) {
        this.calcSize(groupNode, group, graphEditor);
    }

    calcSize(groupNode: Node, groupId: string, graphEditor: GraphEditor) {
        if (graphEditor.groupingManager.getAllChildrenOf(groupId).size > 0) {
            groupNode.height = graphEditor.groupingManager.getAllChildrenOf(groupId).size * 70;
        } else {
            groupNode.height = 20;
        }
        groupNode.width = 140;
    }

    onNodeMoveEnd(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor) {
        repositionGroupNode(group, groupNode, graphEditor);
    }
}

// reposition the groups parent node if one child element changed position
function repositionGroupNode(group: string, groupNode: Node, graphEditor: GraphEditor) {
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
    groupNode.height = minBox.height;

    // set config moveChildrenAlongGoup to false, to position group node around children, and set config back
    const tempConfig = graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup;
    graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup = false;
    graphEditor.moveNode(groupNode.id, minBox.x - boundingBoxBorder, minBox.y - boundingBoxBorder, false);
    graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup = tempConfig;

    graphEditor.completeRender();
}

@autoinject
export class OntologyGraph {
    @bindable isLoading = true;
    @bindable isRendered = false;
    @bindable apiLink;
    @bindable ignoreCache = false;
    @bindable maximizeMenu = false;

    @observable() searchtext: String = "";
    @observable() selectedNode: DataItemModel;
    @observable() typeChildsToShow: number = 3;
    @observable() showTaxonomies: boolean = true;
    @observable() showTypes: boolean = true;
    @observable() showSelectedItems: boolean = false;
    @observable() showElementsWithoutAnEdge: boolean = false;
    @observable() selectedLayoutAlgorithmId: number = 1;
    @observable() distanceBetweenElements: number = 100;
    @observable() keepSearchResultsInFocus: boolean = false;
    @observable() currentEdgeStyleBold: boolean = true;

    @observable graph: GraphEditor;
    @observable graphoverview: GraphEditor;
    @child("div#mainontology-graph") maindiv: any;

    private layoutAlgorithms = [
        { id: 0, name: 'ngraph.forcedirected' },
        { id: 1, name: 'd3-force' },
    ];

    private totalTypes = 0;
    private totalTaxonomies = 0;
    private taxonomyChildItems:number;

    private maximized: boolean = false;
    private isAllowedToShowGraph: boolean = false;

    private missingParentConnection: Array<{ parent: number | string, child: number | string, joinTree: boolean }> = [];

    dataItems: Array<DataItemModel> = [];

    private api: BaseApiService;
    private navService: NavigationLinksService;
    private events: EventAggregator;
    private subscription: Subscription;

    constructor(baseApi: BaseApiService, navService: NavigationLinksService, events: EventAggregator, bindingEngine: BindingEngine) {
        this.api = baseApi;
        this.navService = navService;
        this.checkNavigationLinks();
        this.events = events;
        this.subscribe();

    }

    private subscribe() {
        this.subscription = this.events.subscribe(NAV_LINKS_CHANNEL, (navLinks: NavLinks) => {
            this.checkNavigationLinks();
        });
    }

    // check if the user is allowed to see the ontology graph
    private checkNavigationLinks() {
        if (true && this.navService.getCurrentNavLinks().nav?.length > 0) {
            if (this.navService.getCurrentNavLinks().nav.some(link => link.apiLink.resourceType == "ont-taxonomy") &&
                this.navService.getCurrentNavLinks().nav.some(link => link.apiLink.resourceType == "ont-type")) {
                this.isAllowedToShowGraph = true;
            } else {
                this.isAllowedToShowGraph = false;
            }
        }
    }

    apiLinkChanged(newValue: ApiLink, oldValue) {
        if (newValue == null) {
            return;
        }
        this.loadData(this.ignoreCache);
    }

    maindivChanged(newValue: any) {
        console.log("Found")
        if (newValue.getElementsByClassName("graphoverview").length > 0) {
            console.log("Found1")
            this.graphoverview = newValue.getElementsByClassName("graphoverview")[0]
        } else {
            throw new Error("No graphoverview element in DOM found")
        }
        if (newValue.getElementsByClassName("maingraph").length > 0) {
            console.log("Found2")
            this.graph = newValue.getElementsByClassName("maingraph")[0]
        } else {
            throw new Error("No graph element in DOM found")
        }
    }

    graphChanged(newGraph: GraphEditor, oldGraph) {
        if (newGraph == null) {
            return;
        }
        newGraph.addEventListener("nodeclick", (event) => this.onNodeClick(event as any));
        newGraph.addEventListener("edgeclick", (event) => this.onEdgeClick(event as any));
        newGraph.addEventListener("backgroundclick", (event) => this.onBackgroundClick(event as any));
        newGraph.addEventListener("zoomchange", (event) => this.onZoomChange(event as any));
        newGraph.addEventListener("nodeadd", (event) => this.onNodeAdd(event as any));

        newGraph.dynamicTemplateRegistry.addDynamicTemplate('type-group-node-template', new TypeNodeTemplate);
        newGraph.dynamicTemplateRegistry.addDynamicTemplate('taxonomy-group-node-template', new TaxonomyNodeTemplate);

        newGraph.setEdgeClass = (className, edge, sourceNode, targetNode) => {
            if (targetNode == null) {
                return false;
            }
            return className === targetNode.type;
        }
    }

    graphoverviewChanged(newGraph: GraphEditor, oldGraph) {
        if (newGraph == null) {
            return;
        }
        newGraph.dynamicTemplateRegistry.addDynamicTemplate('overview-node-template', new OverviewGraphNode);
        newGraph.dynamicTemplateRegistry.addDynamicTemplate('type-group-node-template', new TypeNodeTemplate);
        newGraph.dynamicTemplateRegistry.addDynamicTemplate('taxonomy-group-node-template', new TaxonomyNodeTemplate);

    }

    selectedLayoutAlgorithmIdChanged() {
        this.calculateNodePositions();
    }

    distanceBetweenElementsChanged() {
        this.calculateNodePositions();
    }

    searchtextChanged(newText: string, old: string) {
        if (this.graph == null) {
            return;
        }

        this.dataItems.forEach(parent => {
            parent.visible = true
            if (parent.name.toLowerCase().includes(newText.toLowerCase()) && newText != "") {
                parent.isSearchResult = true;
                this.graph.selectNode(parent.id)
            }
            else {
                parent.isSearchResult = false;
                if (!parent.isSelected) {
                    this.graph.deselectNode(parent.id)
                }
            }
            let closeParent = true;
            parent.children.forEach(child => {
                parent.childIsInResult = false;
                if (child.name.toLowerCase().includes(newText.toLowerCase()) && newText != "") {
                    child.isSearchResult = true;
                    this.graph.selectNode(child.id)
                    closeParent = false;
                    parent.childIsInResult = true;
                    if (!parent.expanded) parent.toggleNode();
                }
                else {
                    child.isSearchResult = false;
                    if (!child.isSelected) {
                        this.graph.deselectNode(child.id)
                    }
                    else {
                        closeParent = false;
                    }
                }
            })

            if (parent.expanded && closeParent) {
                parent.toggleNode();
            }
            if (closeParent && newText != "") {
                parent.visible = false
            }
        })
        this.graph.updateHighlights();
        this.graph.getSVG().selectAll("g.node").nodes().forEach(node => {
            if (this.graph.selected.has(node.id.substring(5)) || newText == "") {
                node.classList.remove("greyedout-node")
            } else {
                node.classList.add("greyedout-node")
            }
        });
    }

    keepSearchResultsInFocusChanged(newValue: boolean, oldValue: boolean) {
        if (!newValue && this.graph != null) {
            this.removeSearchResultsHighlighting();
        }
    }

    typeChildsToShowChanged(newValue: number, oldValue: number) {
        if (oldValue == newValue || this.graph == null) return;
        this.dataItems?.filter(p => !p.abstract).filter(p => p.itemType == DataItemTypeEnum.TypeItem).forEach(parent => {
            let childrend = parent.children;
            childrend.forEach(childItem => {
                this.graph.groupingManager.removeNodeFromGroup(parent.id, childItem.id);
                this.graph.removeNode(childItem.id);
            })

            let nodeBox: { x, y } = { x: parent.node.x + 20, y: parent.node.y + 20 };
            let counter = 0;
            parent.children.forEach(childItem => {
                if (counter >= this.typeChildsToShow) return;
                counter++;
                nodeBox = this.addItemsToType(childItem, nodeBox, parent);

            });
        });
        this.postRender();
    }

    showTaxonomiesChanged(value: boolean) {
        if (this.graph == null) {
            return;
        }
        this.showElementsWithoutAnEdge = false;
        this.showSelectedItems = false;
        if (value) {
            this.dataItems.filter(p => p.itemType == DataItemTypeEnum.TaxonomyItem).forEach(p => {
                p.isVisibleInGraph = true
                p.children?.forEach(child => child.isVisibleInGraph = true);
            });
        } else {
            this.dataItems.filter(p => p.itemType == DataItemTypeEnum.TaxonomyItem).filter(p => !p.isSelected).forEach(p => {
                p.isVisibleInGraph = false
                p.children?.forEach(child => child.isVisibleInGraph = false);
            });
        }
        this.updateVisibilityInGraph();
    }

    showTypesChanged(value: boolean) {
        if (this.graph == null) {
            return;
        }
        if (value) {
            this.dataItems.filter(p => p.itemType == DataItemTypeEnum.TypeItem).forEach(p => {
                p.isVisibleInGraph = true
                p.children?.forEach(child => child.isVisibleInGraph = true);
            });
            this.showElementsWithoutAnEdge = false;
            this.showSelectedItems = false;
        } else {
            this.dataItems.filter(p => p.itemType == DataItemTypeEnum.TypeItem).filter(p => !p.isSelected).forEach(p => {
                p.isVisibleInGraph = false
                p.children?.forEach(child => child.isVisibleInGraph = false);
            });
        }
        this.updateVisibilityInGraph();
    }

    showElementsWithoutAnEdgeChanged(value: boolean) {
        if(value && this.graph!=null) {
            this.showSelectedItems = false;
            this.showAllElementsWithoutEdge();
        }

    }

    showSelectedItemsChanged(value: boolean) {
        if(value && this.graph!=null) {
            this.showElementsWithoutAnEdge = false;
            this.showSelectedItemsFunction();
        }
    }

    /**
     * load the data from the server, links are given by the navigation service
     * @param ignoreCache 
     */
    private loadData(ignoreCache: boolean) {
        console.log("Start loading data")
        if (this.navService.getCurrentNavLinks().nav.some(link => link.apiLink.resourceType == "ont-type")) {
            this.loadDataTypes(this.navService.getCurrentNavLinks().nav.find(link => link.apiLink.resourceType == "ont-type").apiLink, this.ignoreCache);
        }
        if (this.navService.getCurrentNavLinks().nav.some(link => link.apiLink.resourceType == "ont-taxonomy")) {
            this.loadDataTaxonomy(this.navService.getCurrentNavLinks().nav.find(link => link.apiLink.resourceType == "ont-taxonomy").apiLink, this.ignoreCache);
        }
    }

    /**
     * load all type items of the namespace
     * @param rootLink root link from the navigation-service
     * @param ignoreCache 
     */
    private loadDataTypes(rootLink: ApiLink, ignoreCache: boolean) {
        this.api.getByApiLink<TypeApiObject>(rootLink, ignoreCache).then(apiResponse => {
            apiResponse.links.forEach(link => {
                if (link.rel.includes("next")) {
                    this.loadDataTypes(link, this.ignoreCache);
                }
            })
            this.totalTypes = apiResponse.data.collectionSize;
            const promisesTypes = [];
            // for each type in namespace
            apiResponse.data.items?.forEach(element => {
                // load each type of the namespace
                promisesTypes.push(this.api.getByApiLink<TypeItemApiObject>(element, ignoreCache).then(apiResponse => {
                    let data = apiResponse.data;
                    let nodeID = this.createUniqueId(data.self.href);
                    this.dataItems.push(new DataItemModel(nodeID, data.name, data.abstract, data.self.href, data.schema.description, DataItemTypeEnum.TypeItem, this.graph));
                    for (let typeElement in data.schema.definitions?.root?.properties) {
                        let typeProps = data.schema.definitions?.root?.properties[typeElement];
                        let typeEnum = this.mapTypeEnums(data.schema.definitions?.root?.properties[typeElement]);
                        let typeHref = ""
                        if (typeEnum == DataItemTypeEnum.TypeProperty) {
                            typeHref = this.getTypeHref(typeProps["referenceKey"]["namespaceId"], typeProps["referenceKey"]["typeId"])
                        } else if (typeEnum == DataItemTypeEnum.TaxonomyProperty) {
                            typeHref = this.getTaxonomyHref(typeProps["referenceKey"]["namespaceId"], typeProps["referenceKey"]["taxonomyId"]);
                        } else {
                            typeHref = nodeID + "-" + typeElement;
                        }

                        let childID = this.createUniqueId(typeHref)
                        this.dataItems.find(p => p.id == nodeID).addChild(childID, typeElement, false, typeHref, "tbd", typeEnum);
                    }
                }));
            });
            Promise.all(promisesTypes).then(() => {
                console.log("done with all type data", this.dataItems.length, this.totalTypes)
                if (this.dataItems.length == this.totalTypes + this.totalTaxonomies) {
                    this.preRenderGraph();
                }
            });

        });
    }


    /**
     * load all taxonomy items of the namespace
     * @param rootLink root link from the navigation-service
     * @param ignoreCache 
     */
    private loadDataTaxonomy(rootLink: ApiLink, ignoreCache: boolean) {
        this.api.getByApiLink<TaxonomyApiObject>(rootLink, ignoreCache).then(apiResponse => {
            apiResponse.links.forEach(link => {
                if (link.rel.includes("next")) {
                    this.loadDataTaxonomy(link, this.ignoreCache);
                }
            })
            this.totalTaxonomies = apiResponse.data.collectionSize;
            const promises = [];
            // for each taxonomy in namespace
            apiResponse.data.items.forEach(element => {
                promises.push(this.api.getByApiLink<TaxonomyApiObject>(element, ignoreCache).then(apiResponse => {
                    let nodeID = this.createUniqueId(apiResponse.data.self.href);
                    this.dataItems.push(new DataItemModel(nodeID, apiResponse.data.name, false, apiResponse.data.self.href, apiResponse.data.description, DataItemTypeEnum.TaxonomyItem, this.graph))
                    let taxonomyItems:TaxonomyItemApiObject[] = []
                    apiResponse.data.items.forEach(element => {
                        this.api.getByApiLink<TaxonomyItemApiObject>(element, ignoreCache).then(apiResponse => {
                            taxonomyItems.push(apiResponse.data)
                        }).then(()=>{
                            if(taxonomyItems.length==apiResponse.data.items.length){
                                let relationLinks: ApiLink[] = [];
                                let relationItems:TaxonomyItemRelationApiObject[] = []
                                taxonomyItems.forEach(tax => {
                                    relationLinks.push(...tax.children)
                                })
                                relationLinks.forEach(link => {
                                    this.api.getByApiLink<TaxonomyItemRelationApiObject>(link, ignoreCache).then(apiResponses => {
                                        relationItems.push(apiResponses.data)
                                    }).then(() => {
                                        if(relationItems.length==relationLinks.length) {
                                            let taxonomyDataItems: DataItemModel[] = []
                                            taxonomyItems.forEach(item => taxonomyDataItems.push(new DataItemModel(this.createUniqueId(item.self.href), item.name, false, item.self.href, item.description, DataItemTypeEnum.TaxonomyItemProperty, this.graph, false)))
                                            taxonomyItems.filter(item => item.deletedOn==null).filter(item => item.isToplevelItem).forEach(item => {
                                                let parent = taxonomyDataItems.find(dataItem => dataItem.href == item.self.href)
                                                this.createTaxonomyHierarchie(parent, item, taxonomyItems, relationItems, taxonomyDataItems);
                                                this.dataItems.find(p => p.id == nodeID).addChildItem(parent);
                                            })
                                        }
                                    })
                                });
                            }
                        });
                    });
                }));
            });
            Promise.all(promises).then(() => {
                console.log("done with all tax data", this.dataItems.length)
                if (this.dataItems.length == this.totalTypes + this.totalTaxonomies) {
                    this.preRenderGraph();
                }
            });
        })
    }

    private createTaxonomyHierarchie(parent: DataItemModel, item: TaxonomyItemApiObject, allItems: TaxonomyItemApiObject[], allRelations: TaxonomyItemRelationApiObject[], taxonomyDataItems: DataItemModel[]) {
        item.children.forEach(child => {
            let targetChild = allRelations.find(item => item.self.href == child.href).targetItem;
            let targetItem = allItems.find(item => item.self.href == targetChild.href);
            //let childItem = new DataItemModel(this.createUniqueId(targetItem.self.href), targetItem.name, false, targetItem.self.href, targetItem.description, DataItemTypeEnum.TaxonomyItemProperty, this.graph, false);
            let childItem = taxonomyDataItems.find(dataItem => dataItem.href == targetItem.self.href)
            parent.addChildItem(childItem);
            this.createTaxonomyHierarchie(childItem, targetItem, allItems, allRelations, taxonomyDataItems);                       
        })
    }

 


    /**
     * get the corresponding DataItemTypeEnum from the api response for a given element to store the correct value in the datamodel
     * @param type type from the api response
     * @returns the corresponding DataItemTypeEnum
     */
    private mapTypeEnums(type: any): DataItemTypeEnum {
        if (type["type"] == "object") {
            if (type["referenceType"] == "ont-taxonomy") {
                return DataItemTypeEnum.TaxonomyProperty;
            } else if (type["referenceType"] == "ont-type") {
                return DataItemTypeEnum.TypeProperty;
            } else {
                return DataItemTypeEnum.Undefined;

            }
        } else if (type["enum"]) {
            return DataItemTypeEnum.EnumProperty;
        } else {
            if (type["type"] == "string") {
                return DataItemTypeEnum.StringProperty;
            } else if (type["type"] == "integer") {
                return DataItemTypeEnum.IntegerProperty;
            } else if (type["type"] == "boolean") {
                return DataItemTypeEnum.BooleanProperty;
            } else if (type["type"] == "number") {
                return DataItemTypeEnum.NumberProperty;
            }
            else {
                return DataItemTypeEnum.Undefined;
            }
        }
    }

    /**
     * if the focus of the searchtext input box is left, decide to show all elements normal or keep it as it is
     */
    searchtextFocusLeft() {
        if (!this.keepSearchResultsInFocus && this.graph != null) {
            this.removeSearchResultsHighlighting();
        }
    }

    /**
     * remove the searchresult higlighting
     */
    removeSearchResultsHighlighting() {
        this.graph.getSVG().selectAll("g.node").nodes().forEach(node => node.classList?.remove("greyedout-node"));
        this.dataItems.forEach(par => {
            par.isSearchResult = false;
            par.childIsInResult = false;
            par.visible = true;
            if (!par.isSelected) this.graph.deselectNode(par.id)
            let collapse: boolean = true;
            par.children.forEach(child => {
                child.isSearchResult = false;
                if (!child.isSelected) this.graph.deselectNode(child.id)
                if (child.isSelected) collapse = false;
            });
            if (collapse && par.expanded) {
                par.toggleNode();
            }
        });
        this.graph.updateHighlights();
    }

    /**
     * show all elements without an connected edge
     */
    showAllElementsWithoutEdge() {
        // get all edge connections in a list
        let allEdgeConnections = []
        this.graph.edgeList.forEach(edge => allEdgeConnections.push(edge.target, edge.source));

        // set the checkboxes to false
        this.showTypes = false
        this.showTaxonomies = false

        // check all parent items, if they are in the list of edge connections and decide to show or hide
        this.dataItems.forEach(parent => {
            parent.isVisibleInGraph = true;
            parent.children?.forEach(child => child.isVisibleInGraph = true);

            if (allEdgeConnections.includes(parent.id)) {
                parent.isVisibleInGraph = false;
                parent.children?.forEach(child => child.isVisibleInGraph = false);
            }

            parent.children.forEach(child => {
                if (allEdgeConnections.includes(child.id)) {
                    parent.isVisibleInGraph = false;
                    parent.children?.forEach(child => child.isVisibleInGraph = false);
                }
            })
        })
        this.updateVisibilityInGraph();
    }

    /**
     * calcualte the position of the nodes based on the selected layout algorithm
     */
    private calculateNodePositions() {
        if (this.graph == null) {
            return;
        }
        if (this.selectedLayoutAlgorithmId == 0) {
            this.calculateNodePositionsNgraph();
        } else if (this.selectedLayoutAlgorithmId == 1) {
            this.calculateNodePositionsd3();
        }
    }

    /**
     * calculate the nodes position based on the ngraph.forcedirected algorithm
     * store the positions in each node
     */
    private calculateNodePositionsNgraph() {
        let createGraph = require('ngraph.graph');
        let g = createGraph();

        this.dataItems.filter(item => item.isVisibleInGraph).forEach(item => g.addNode(item.id))

        this.dataItems.filter(p => p.isVisibleInGraph).forEach(parItem => {
            parItem.children.filter(p => p.isVisibleInGraph).forEach(child => {
                if (child.itemType == DataItemTypeEnum.TaxonomyProperty || child.itemType == DataItemTypeEnum.TypeProperty) {
                    this.dataItems.filter(p => p.isVisibleInGraph).forEach(parent => {
                        if (child.id.startsWith(parent.id.split("-")[0])) {
                            g.addLink(parItem.id, parent.id)
                        }
                    });
                }
            });
        });

        let physicsSettings = {
            timeStep: 0.5,
            dimensions: 2,
            gravity: -12,
            theta: 0.8,
            springLength: 50,
            springCoefficient: 0.8,
            dragCoefficient: 0.9,
        };
        let positionDifference = 20 * (this.distanceBetweenElements / 100);

        let createLayout = require('ngraph.forcelayout');
        let layout = createLayout(g, physicsSettings);
        this.dataItems.filter(item => item.positionIsFixed).forEach(item => {
            if(item.node==null) return
            layout.setNodePosition(item.id, item.node.x, item.node.y);
            var node = g.getNode(item.id);
            layout.pinNode(node, true); // toggle it
        });
        for (var i = 0; i < 500; ++i) {
            layout.step();
        }

        g.forEachNode(node => {
            let pos = layout.getNodePosition(node.id);
            let nodeToPin = g.getNode(node.id);
            if (layout.isNodePinned(node)) {
                this.dataItems.find(el => el.id == node.id).position = { x: pos.x, y: pos.y }
            } else {
                this.dataItems.find(el => el.id == node.id).position = { x: pos.x * positionDifference, y: pos.y * positionDifference }
            }
        });
    }

    /**
     * calculate the nodes position based on the d3-force algorithm
     * store the positions in each node
     */
    private calculateNodePositionsd3() {
        let links = [];
        let nodes = [];

        this.dataItems.filter(item => item.isVisibleInGraph).forEach(item => nodes.push({ id: item.id, radius: this.calcRadius(item) }))
        this.dataItems.filter(p => p.isVisibleInGraph).forEach(parItem => {
            parItem.children.filter(p => p.isVisibleInGraph).forEach(child => {
                if (child.itemType == DataItemTypeEnum.TaxonomyProperty || child.itemType == DataItemTypeEnum.TypeProperty) {
                    this.dataItems.filter(p => p.isVisibleInGraph).forEach(parent => {
                        if (child.id.startsWith(parent.id.split("-")[0])) {
                            links.push({ target: parItem.id, source: parent.id })
                        }
                    });
                }
            });
        });

        this.dataItems.filter(item => item.positionIsFixed).forEach(item => {
            if(item.node==null) return
            nodes.find(x => x.id == item.id).fx = item.node.x;
            nodes.find(x => x.id == item.id).fy = item.node.y;
        });

        forceSimulation(nodes)
            .force("link", forceLink(links).id(d => d.id))
            .force("charge", forceManyBody())
            .force("center", forceCenter(this.graph.currentViewWindow.width / 2, this.graph.currentViewWindow.height / 2))
            .force('collision', forceCollide().radius(d => this.calcRadius(d)))
            .stop()
            .tick(100);

        let positionDifference = 1.3 * (this.distanceBetweenElements / 100);

        nodes.forEach(x => {
            if (this.dataItems.find(y => y.id == x.id).positionIsFixed) {
                this.dataItems.find(y => y.id == x.id).position = { x: x.x, y: x.y };
            } else {
                let dx = this.calcRadius(this.dataItems.find(y => y.id == x.id));
                let dy = this.calcRadius(this.dataItems.find(y => y.id == x.id));
                this.dataItems.find(y => y.id == x.id).position = { x: (x.x - dx) * positionDifference, y: (x.y - dy) * positionDifference };
            }
        })

    }

    /**
     * calculate the radius for a given node for a good layouting with d3-force
     * @param d node of the graph
     * @returns radius of the given node
     */
    private calcRadius(d) {
        if (this.dataItems.find(x => x.id == d.id).itemType == DataItemTypeEnum.TaxonomyItem) {
            return 130;
        } else if (this.dataItems.find(x => x.id == d.id).itemType == DataItemTypeEnum.TypeItem) {
            if (this.dataItems.find(x => x.id == d.id).children.length > 2) {
                return 165;
            } else if (this.dataItems.find(x => x.id == d.id).children.length > 1) {
                return 130;
            } else if (this.dataItems.find(x => x.id == d.id).children.length > 0) {
                return 95;
            }
            return 60;
        }
    }

    /**
     * sort all dataitems in an alphabetical order
     * @param items dataitems list
     */
    private sortList(items: DataItemModel[]) {
        items.sort(function (a, b) {
            var nameA = a.name.toUpperCase(); // ignore upper and lowercase
            var nameB = b.name.toUpperCase(); // ignore upper and lowercase
            if (nameA < nameB) {
                return -1;
            }
            if (nameA > nameB) {
                return 1;
            }

            // names must be equal
            return 0;
        });
        items.forEach(item => this.sortList(item.children))
    }

    /**
     * complete graph rendering
     */
    private postRender() {
        this.graph.completeRender();
        this.graphoverview.completeRender();
        this.addChildnodesToParents();

        this.updateHiddenLinks();

        this.graph.completeRender();
        this.graphoverview.completeRender();

        let svgOverviewgraph = this.graphoverview.getSVG().select("g.zoom-group");
        svgOverviewgraph.append("g")
            .attr("id", "overviewrect").append("rect");

        this.isLoading = false;
        this.isRendered = true;
    }

    /**
     * update the visibility of all nodes in the graph based on the dataitems isVisibleInGraph value
     */
    private updateVisibilityInGraph() {
        this.graph.getSVG().selectAll("g.edge-group").nodes().forEach(edge => {
            edge.classList?.remove("invisible-node")
        });

        this.dataItems.forEach(node => {
            if (node.isVisibleInGraph) {
                this.graph.getSVG().select("#node-" + node.id).node()?.classList?.remove("invisible-node")
                this.graphoverview.getSVG().select("#node-" + node.id).node()?.classList?.remove("invisible-node")
            } else {
                this.graph.getSVG().select("#node-" + node.id).node()?.classList?.add("invisible-node")
                this.graphoverview.getSVG().select("#node-" + node.id).node()?.classList?.add("invisible-node")
                this.updateVisibilityOfEdge(node.id, false)
            }
            node.children.forEach(child => {
                if (child.isVisibleInGraph) {
                    this.graph.getSVG().select("#node-" + child.id).node()?.classList?.remove("invisible-node")
                    this.graphoverview.getSVG().select("#node-" + child.id).node()?.classList?.remove("invisible-node")
                } else {
                    this.graph.getSVG().select("#node-" + child.id).node()?.classList?.add("invisible-node")
                    this.graphoverview.getSVG().select("#node-" + child.id).node()?.classList?.add("invisible-node")
                    this.updateVisibilityOfEdge(child.id, false)
                }
            });
        })
    }

    /**
     * update the visibility of an edge in the graph
     * @param nodeid all edges of this id should be hidden or shown, based on the visibile param
     * @param visibile show or hide the edges
     */
    private updateVisibilityOfEdge(nodeid: string, visibile: boolean) {
        this.graph.getSVG().selectAll("g.edge-group").nodes().forEach(edge => {
            if (edge.id.includes(nodeid)) {
                if (visibile) {
                    edge.classList?.remove("invisible-node")
                } else {
                    edge.classList?.add("invisible-node")
                }
            }
        });
        this.graphoverview.getSVG().selectAll("g.edge-group").nodes().forEach(edge => {
            if (edge.id.includes(nodeid)) {
                if (visibile) {
                    edge.classList?.remove("invisible-node")
                } else {
                    edge.classList?.add("invisible-node")
                }
            }
        });
    }

    /**
     * reposition all nodes back to the calculated positions
     */
    repositionNodes() {
        this.dataItems.filter(p => !p.abstract).forEach(parent => {
            this.graph.moveNode(parent.id, parent.position.x, parent.position.y)
            this.graphoverview.moveNode(parent.id, parent.position.x, parent.position.y)
        })
        this.graph.completeRender();
        this.resetLayout();
        this.addInvisibleRectToOverview();
        this.graphoverview.completeRender();
        this.graphoverview.zoomToBoundingBox(true);
    }

    private async preRenderGraph() {
        this.calculateNodePositions();
        this.sortList(this.dataItems);
        this.isLoading = false;
    }



    private async renderTypes() {
        await this.dataItems?.forEach(element => {
            if (element.itemType == DataItemTypeEnum.TypeItem && !element.abstract) {
                this.addTypeItem(element);
            }
        });
    }

    private async renderTaxonomies() {
        await this.dataItems?.forEach((element) => {
            if (element.itemType == DataItemTypeEnum.TaxonomyItem) {
                this.addTaxonomyItem(element);
            }
        });
    }

    private updateHiddenLinks() {
        if (this.graph == null) {
            return;
        }
        this.dataItems.forEach(parItem => {
            parItem.children.forEach(child => {
                if (child.itemType == DataItemTypeEnum.TaxonomyProperty || child.itemType == DataItemTypeEnum.TypeProperty) {
                    this.dataItems.forEach(parent => {
                        if (child.id.startsWith(parent.id.split("-")[0])) {
                            let source: string;
                            if (this.graph.nodeList.some(node => node.id == child.id)) {
                                source = child.id;
                                if (this.graph.edgeList.find(p => p.source == parItem.id && p.target == parent.id)) {
                                    this.graph.removeEdge(this.graph.edgeList.find(p => p.source == parItem.id && p.target == parent.id));
                                }
                            } else {
                                // choose parent-item
                                source = parItem.id;
                            }

                            let path = {
                                source: source, target: parent.id, markerEnd: {
                                    template: "arrow",
                                    scale: largeMarkerSize,
                                    relativeRotation: 0,
                                },
                                id: source + parent.id
                            }

                            let pathOverview = {
                                source: parItem.id, target: parent.id, markerEnd: {
                                    template: "arrow",
                                    scale: largeMarkerSize,
                                    relativeRotation: 0,
                                },
                                id: parItem.id + parent.id
                            }

                            if (!this.graph.edgeList.some(p => p.source == source && p.target == parent.id) &&
                                this.graph.nodeList.some(p => p.id == path.source) &&
                                this.graph.nodeList.some(p => p.id == path.target)) {
                                this.graph.addEdge(path, false)
                                this.graphoverview?.addEdge(pathOverview, false)
                            }
                        }
                    });
                }
            })
        })
    }

    private async addChildnodesToParents() {
        while (this.missingParentConnection.length != 0) {
            let node = this.missingParentConnection.pop();
            this.graph.groupingManager.addNodeToGroup(node.parent, node.child);
            if (node.joinTree) {
                this.graph.groupingManager.joinTreeOfParent(node.child, node.parent); //WHY???
            }
        }
    }

    private getTaxonomyHref(namespaceId: number, taxonomyID: number): string {
        return "http://localhost:5000/api/v1/namespaces/" + namespaceId + "/taxonomies/" + taxonomyID + "/";
    }

    private getTypeHref(namespaceId: number, typeID: number): string {
        return "http://localhost:5000/api/v1/namespaces/" + namespaceId + "/types/" + typeID + "/";
    }

    private addTypeItem(parentItem: DataItemModel): { x, y } {
        let parentPosition = parentItem.position;
        parentPosition.x = parentPosition.x + boundingBoxBorder;
        parentPosition.y = parentPosition.y + boundingBoxBorder;
        let groupManager = this.graph.groupingManager;
        let parentBox = this.addNodeToGraph({ id: parentItem.id, title: parentItem.name, dynamicTemplate: "type-group-node-template", ...parentPosition }, false);

        groupManager.markAsTreeRoot(parentItem.id);
        groupManager.setGroupBehaviourOf(parentItem.id, new TypeGroupBehaviour());

        // check if type has properties
        if (parentItem.children.length == 0) {
            return;
        }

        // sore previous nodes values
        let nodeBox: { x, y } = { x: parentBox.x + 20, y: parentBox.y + 20 };
        let counter = 0;
        parentItem.children.forEach(childItem => {
            if (counter >= this.typeChildsToShow) return;
            counter++;
            nodeBox = this.addItemsToType(childItem, nodeBox, parentItem);

        });
        return this.getLeftBottomPointOfItem(parentItem.node);
    }

    private addItemsToType(childItem: DataItemModel, nodeBox: { x, y }, parentItem: DataItemModel): { x, y } {
        if (childItem.itemType == DataItemTypeEnum.TaxonomyProperty) {
            nodeBox = this.addNodeToGraph({ id: childItem.id, title: childItem.name, type: "taxonomy-link-item", x: nodeBox.x, y: nodeBox.y, typedescription: "Taxonomy-Ref", typedescriptionHref: "#" + childItem.itemType }, false);
        } else if (childItem.itemType == DataItemTypeEnum.TypeProperty) {
            nodeBox = this.addNodeToGraph({ id: childItem.id, title: childItem.name, type: "type-link-item", x: nodeBox.x, y: nodeBox.y, typedescription: "Type-Ref", typedescriptionHref: "#" + childItem.itemType }, false);
        } else if (childItem.itemType == DataItemTypeEnum.EnumProperty ||
            childItem.itemType == DataItemTypeEnum.BooleanProperty ||
            childItem.itemType == DataItemTypeEnum.IntegerProperty ||
            childItem.itemType == DataItemTypeEnum.NumberProperty ||
            childItem.itemType == DataItemTypeEnum.StringProperty ||
            childItem.itemType == DataItemTypeEnum.Undefined) {
            nodeBox = this.addNodeToGraph({ id: childItem.id, title: childItem.name, type: "type-item", x: nodeBox.x, y: nodeBox.y, typedescription: childItem.itemType, typedescriptionHref: "#" + childItem.itemType }, false);
        }
        this.missingParentConnection.push({ parent: parentItem.id, child: childItem.id, joinTree: false })
        return nodeBox;
    }

    private addTaxonomyItem(parentItem: DataItemModel): { x, y } {
        let parentPosition = parentItem.position;
        parentPosition.x = parentPosition.x + boundingBoxBorder;
        parentPosition.y = parentPosition.y + boundingBoxBorder;

        this.addNodeToGraph({ id: parentItem.id, title: parentItem.name, dynamicTemplate: "taxonomy-group-node-template", ...parentPosition }, false);

        let groupManager = this.graph.groupingManager;
        groupManager.markAsTreeRoot(parentItem.id);
        groupManager.setGroupBehaviourOf(parentItem.id, new TaxonomyGroupBehaviour());
        
        return this.getLeftBottomPointOfItem(parentItem.node);
    }
    
    private addItemsToTaxonomy(taxonomyParent: DataItemModel, parentBox: { x, y }) {
        if (taxonomyParent == null) {
            throw new Error("No taxonomy parent item available");
        }
        // needed to change between upper and lower new taxonomy item
        let taxonomyItemSize = this.getSizeOfStaticTemplateNode('taxonomy-item');

        this.taxonomyChildItems=0;
        let itemsPerColumn = Math.max(2, Math.round(Math.sqrt(this.getNumberOfTaxonomieItems(taxonomyParent) / 2)))
        taxonomyParent.children.forEach(childElement => {
            this.addNodeToGraph({ id: childElement.id, title: childElement.name, type: 'taxonomy-item', x: parentBox.x + 150 + itemsPerColumn * 23 + (Math.floor(this.taxonomyChildItems / itemsPerColumn)) * (Number(taxonomyItemSize.width) + 10), y: parentBox.y + 20 + itemsPerColumn * 15 + (this.taxonomyChildItems % itemsPerColumn) * (Number(taxonomyItemSize.height) + 10) }, false);
            this.missingParentConnection.push({ parent: taxonomyParent.id, child: childElement.id, joinTree: false })
            this.taxonomyChildItems++;
            this.addRecursiveItemsToTaxonomy(taxonomyParent, childElement, parentBox, itemsPerColumn, taxonomyItemSize)
        });
    }

    private getNumberOfTaxonomieItems(element: DataItemModel): number {
        let value = 0;
        element.children.forEach(item => value += this.getNumberOfTaxonomieItems(item))
        return element.children.length + value
    }

    private addRecursiveItemsToTaxonomy(rootElement: DataItemModel, element: DataItemModel, parentBox: {x,y}, itemsPerColumn, taxonomyItemSize: {width, height}) {
        element.children.forEach(childElement => {
            let node = this.graph.nodeList.find(node => node.id.toString().split("-SPLITTER-")[0]== childElement.id.split("-SPLITTER")[0])
            if(node!=null) {
                this.addEdgeToTaxonomy(element.id, node.id);
            } else {
                this.addNodeToGraph({ id: childElement.id, title: childElement.name, type: 'taxonomy-item', x: parentBox.x + 150 + itemsPerColumn * 23 + (Math.floor(this.taxonomyChildItems / itemsPerColumn)) * (Number(taxonomyItemSize.width) + 10), y: parentBox.y + 20 + itemsPerColumn * 15 + (this.taxonomyChildItems % itemsPerColumn) * (Number(taxonomyItemSize.height) + 10) }, false);
                this.taxonomyChildItems++;
                this.missingParentConnection.push({ parent: rootElement.id, child: childElement.id, joinTree: false })
                this.addEdgeToTaxonomy(element.id, childElement.id);
            }
            this.addRecursiveItemsToTaxonomy(rootElement, childElement, parentBox, itemsPerColumn, taxonomyItemSize);
        });
    }

    /**
     * add a new node to both graphs, if the node isn't already there
     * @param source source node
     * @param target target node
     */
    private addEdgeToTaxonomy(source: string | number, target: string | number) {
        let path = {
            source: source, target: target, markerEnd: {
                template: "arrow",
                scale: largeMarkerSize,
                relativeRotation: 0,
            },
            id: source.toString() + target.toString()
        }
        this.graph.addEdge(path, false)
    }

    private createUniqueId(nodeID: string): string {
        nodeID = String(nodeID).replace(RegExp(/\/\/|\/|:| /g), "")
        // add some random number (unix time stamp) to the id, no make it unique
        let nodeIdOrig = nodeID;
        nodeID = nodeIdOrig + "-SPLITTER-" + Math.floor(Math.random() * 100 * Date.now())

        while (this.dataItems.some(element => element.id == nodeID)) {
            nodeID = nodeIdOrig + "-SPLITTER-" + Math.floor(Math.random() * 100 * Date.now())
        }
        return nodeID;
    }

    /**
     * add a new node to both graphs, if the node isn't already there
     * @param node, node to add to the graph
     * @returns id of the new added node and the left bottom point of the node
     */
    private addNodeToGraph(node: Node, redrawGraph: boolean): { x: number, y: number } {


        this.connectDataItemWithNode(this.dataItems, node)

        node.y = node.y + 10;

        // if the node template based on a static template, change x and y coordinate to the center of the node
        if (node.type) {
            let { width, height } = this.getSizeOfStaticTemplateNode(node.type);
            node.x = node.x + width / 2;
            node.y = node.y + height / 2;
        }

        if (!this.graph.nodeList.some(existNodes => existNodes.id == node.id)) {
            this.graph?.addNode(node, false);
            //only add root elements to graphoverview
            if (this.dataItems.some(p => p.id == node.id)) {
                this.graphoverview?.addNode(node, false);
            }
        }

        return this.getLeftBottomPointOfItem(node);
    }


    private connectDataItemWithNode(dataItem: DataItemModel[], node: Node) {
        dataItem.forEach(p => {
            if (p.id == node.id) {
                p.node = node;
                return;
            }
            this.connectDataItemWithNode(p.children, node);
        });
    }

    /**
     * get the size of a static template for further calculation
     * @param nodeType, name of the static template
     * @returns size of the node
     */
    private getSizeOfStaticTemplateNode(nodeType: string): { width: number, height: number } {
        let width = this.graph.staticTemplateRegistry.getNodeTemplate(nodeType).node().getElementsByTagName("rect")[0].getAttribute("width");
        let height = this.graph.staticTemplateRegistry.getNodeTemplate(nodeType).node().getElementsByTagName("rect")[0].getAttribute("height");
        return { width, height }
    }

    /**
     * get left bottom point of new added node, for correct positioning of the next node
     * @param nodeID, id of the node as string or number
     * @returns left bottom point of the node {x,y}
     */
    private getLeftBottomPointOfItem(node: Node): { x, y } {

        if (node.type) {
            let { width, height } = this.getSizeOfStaticTemplateNode(node.type);
            return { x: node.x - width / 2, y: node.y + height / 2 }
        } else {
            return { x: node.x, y: node.y }
        }
    }

    private onNodeClick(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node, key: string }>) {
        if (event.detail.eventSource !== "USER_INTERACTION") {
            return;
        }
        event.preventDefault();
        const node = event.detail.node;
        console.log(event)

        if (node.dynamicTemplate === "taxonomy-group-node-template" && event.detail.key == "expandNode") {
            if (this.graph.groupingManager.getAllChildrenOf(node.id).size > 0) {
                this.graph.groupingManager.getAllChildrenOf(node.id).forEach(child => {
                    this.graph.groupingManager.removeNodeFromGroup(node.id, child)
                    this.graph.removeNode(child, false);
                })
                node.childsVisible = false;
                this.graph.completeRender();
                this.graphoverview.completeRender();
            }
            else {
                this.addItemsToTaxonomy(this.dataItems.find(t => t.id == node.id), this.getLeftBottomPointOfItem(node));
                this.graph.completeRender();
                this.addChildnodesToParents();
                this.setCurrentEdgeStyle(this.currentEdgeStyleBold);
                this.graph.completeRender();
                this.graphoverview.completeRender();
            }
        }
        else if (event.detail.key == "header") {
            this.selectedNode = this.dataItems.find(item => item.id == node.id);
        }
        else if (event.type == 'nodeclick') {
            this.graph.edgeList.forEach(edge => {
                this.graph.getSVG().selectAll("g.edge-group").nodes().forEach(edge => {
                    if (edge.id.includes(node.id)) {
                        if(this.currentEdgeStyleBold) {
                            edge.childNodes[0].classList.add("highlight-bold-edge")
                            this.highlightMarker(edge.id.substring(5), "big-arrow", 2.8)
                        } else {
                            edge.childNodes[0].classList.add("highlight-edge")
                            this.highlightMarker(edge.id.substring(5), "big-arrow", 1.8)
                        }
                    }
                    this.dataItems.find(p => p.id == node.id)?.children?.forEach(childNode => {
                        if (edge.id.includes(childNode.id)) {
                            if(this.currentEdgeStyleBold) {
                                edge.childNodes[0].classList.add("highlight-bold-edge")
                                this.highlightMarker(edge.id.substring(5), "big-arrow", 2.8)
                            } else {
                                edge.childNodes[0].classList.add("highlight-edge")
                                this.highlightMarker(edge.id.substring(5), "big-arrow", 1.8)
                            }
                        }
                    })
                });
            })
        }
        this.graph.completeRender();
    }

    private highlightMarker(edgeID, template, scale) {
        this.graph.getEdge(edgeID).markerEnd = {
            template: template,
            scale: scale,
            relativeRotation: 0,
        }
    }

    private onEdgeClick(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node }>) {
        if (event.detail.eventSource !== "USER_INTERACTION") {
            return;
        }
        event.preventDefault();
        const node = event.detail.node;
        if (node.type !== "taxonomy-item") {
            return;
        }
    }

    private onBackgroundClick(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node }>) {
        this.selectedNode = null;
        this.renderMainViewPositionInOverviewGraph();
        this.graph.getSVG().selectAll("g.edge-group").nodes().forEach(edge => {
            edge.childNodes[0].classList.remove("highlight-edge")
            edge.childNodes[0].classList.remove("highlight-bold-edge")
            if(this.currentEdgeStyleBold) {
                this.highlightMarker(edge.id.substring(5), "arrow", largeMarkerSize)
            } else {
                this.highlightMarker(edge.id.substring(5), "small-arrow", smallMarkerSize)
            }
        });
        this.graph.completeRender();
    }

    private onNodeAdd(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node }>) {
        this.addInvisibleRectToOverview();
    }

    private addInvisibleRectToOverview() {
        let currentView = this.graph.currentViewWindow;
        this.graphoverview?.removeNode(42424242424242424242424242424242421, false);
        this.graphoverview?.addNode({ id: 42424242424242424242424242424242421, class: "invisible-rect", dynamicTemplate: 'overview-node-template', x: currentView.x, y: currentView.y, width: currentView.width, height: currentView.height }, false);
    }

    currentEdgeStyleBoldChanged(newValue: boolean) {
        if (this.graph == null) return;
        this.setCurrentEdgeStyle(newValue);
        this.graph.completeRender();
    }

    private setCurrentEdgeStyle(value) {
        if (value) {
            this.graph.getSVG().selectAll("g.edge-group").nodes().forEach(edge => {
                edge.childNodes[0].classList.remove("small-edge")
                this.highlightMarker(edge.id.substring(5), "arrow", largeMarkerSize)
            });
        } else {
            this.graph.getSVG().selectAll("g.edge-group").nodes().forEach(edge => {
                edge.childNodes[0].classList.add("small-edge")
                this.highlightMarker(edge.id.substring(5), "small-arrow", smallMarkerSize)
            });
        }
    }

    private onZoomChange(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node }>) {
        this.renderMainViewPositionInOverviewGraph();
        if(this.graph ==null) return
        if (this.graph.currentViewWindow.width <= document.getElementById('maingraphpart').offsetWidth*2) {
            this.currentEdgeStyleBold = false;

        } else {
            this.currentEdgeStyleBold = true;
        }
    }

    private renderMainViewPositionInOverviewGraph() {
        if (this.graphoverviewChanged == null) {
            return;
        }
        let currentView = this.graph.currentViewWindow;
        let svg = this.graphoverview.getSVG();
        svg.select("g#overviewrect").select("rect")
            .attr("x", currentView.x)
            .attr("y", currentView.y)
            .attr("width", currentView.width)
            .attr("height", currentView.height)
            .attr("class", "position-rect");

    }

    // function called by buttons from the front-end, to interact with the graph
    private zoomIn() {
        let zoomBox = this.graph.currentViewWindow;
        let newBox: Rect = { x: 0, y: 0, width: 0, height: 0 };
        newBox.width = zoomBox.width - zoomBox.width * 0.2;
        newBox.height = zoomBox.height - zoomBox.height * 0.2;
        newBox.x = zoomBox.x + (zoomBox.width - newBox.width) * 0.5;
        newBox.y = zoomBox.y + (zoomBox.height - newBox.height) * 0.5;
        this.graph.zoomToBox(newBox);
    }

    // function called by buttons from the front-end, to interact with the graph
    private zoomOut() {
        let zoomBox = this.graph.currentViewWindow;
        let newBox: Rect = { x: 0, y: 0, width: 0, height: 0 };
        newBox.width = zoomBox.width + zoomBox.width * 0.2;
        newBox.height = zoomBox.height + zoomBox.height * 0.2;
        newBox.x = zoomBox.x + (zoomBox.width - newBox.width) * 0.5;
        newBox.y = zoomBox.y + (zoomBox.height - newBox.height) * 0.5;
        this.graph.zoomToBox(newBox);
    }

    // function called by buttons from the front-end, to interact with the graph
    private toggleMaximize() {
        this.maximized = !this.maximized;
        if(this.maximized) {
            document.getElementById("mainontology-graph").style.height="100%"
            document.getElementById("ontology-graph").style.padding="0px"
        } else {
            document.getElementById("mainontology-graph").style.height="500px"
            document.getElementById("ontology-graph").style.padding=""
        }
        this.graphoverview.zoomToBoundingBox(true);
    }

    // function called by buttons from the front-end, to interact with the graph
    private toggleMenu() {
        this.maximizeMenu = !this.maximizeMenu;
    }

    private fixallSearchResults() {
        this.dataItems.filter(p => p.isSearchResult).forEach(p => p.positionIsFixed = true);
    }

    // function called by buttons from the front-end, to interact with the graph
    private resetLayout() {
        this.graph?.zoomToBoundingBox(true);
    }

    // function called by buttons from the front-end, to interact with the graph
    private moveGraph(direction: String) {
        let dirX = this.graph.currentViewWindow.width / 20;
        let dirY = this.graph.currentViewWindow.height / 20;

        const element = document.getElementById("graphexportsvg").shadowRoot.querySelector(".graph-editor").querySelector("g.zoom-group")
        let transformsettings = element.getAttribute("transform")
        let width: number = Number(transformsettings.split("(")[1].split(",")[0])
        let height: number = Number(transformsettings.split("(")[1].split(",")[1].split(")")[0])
        let scaling = transformsettings.split("(")[2].split(")")[0]

        if (direction == 'down') {
            height += dirY;
        } else if (direction == 'right') {
            width += dirX;
        } else if (direction == 'left') {
            width -= dirX;
        } else if (direction == 'up') {
            height -= dirY;
        }

        element.setAttribute("transform", "translate(" + width + "," + height + ") scale(" + scaling + ")")
    }

    private showSelectedItemsFunction() {
        this.showTypes = false;
        this.showTaxonomies = false;
        this.dataItems.forEach(parent => {
            if (parent.isSelected) {
                parent.isVisibleInGraph = true;
            }
            else {
                parent.isVisibleInGraph = false;
                parent.children.forEach(child => {
                    if (child.isSelected) {
                        child.isVisibleInGraph = true;
                        parent.isVisibleInGraph = true;
                    }
                })
            }
        })
        this.updateVisibilityInGraph();
    }

    unselectNode() {
        this.selectedNode = null;
    }

    private downloadSVG() {
        // TODO: dowload svg
        var PDFDocument = require('pdfkit'),
            SVGtoPDF = require('svg-to-pdfkit');

        var doc = new PDFDocument(),
            stream = fs.createWriteStream('file.pdf');

        SVGtoPDF(doc, this.graph.getSVG, 0, 0);

        stream.on('finish', function () {
            console.log(fs.readFileSync('file.pdf'))
        });

        doc.pipe(stream);
        doc.end();
    }

    storedViewWindow: Rect;

    private tempZoomOut(state) {
        if(state=="on") {
            this.storedViewWindow = this.graph.currentViewWindow;
            this.graph.zoomToBoundingBox();
        } else {
            this.graph.zoomToBox(this.storedViewWindow);
        }
    }

    private renderGraph() {
        this.isLoading = true;

        if (this.graph == null) {
            return;
        }

        if (this.showTypes) this.renderTypes();

        if (this.showTaxonomies) this.renderTaxonomies();
        this.postRender();
        this.resetLayout();

        this.graphoverview.zoomToBoundingBox();
    }

    isMainDragging: boolean = false;
    isLeftUpperDragging: boolean = false;
    isLeftLowerDragging: boolean = false;
    startDraggingPosition;

    endDrag() {
        if(this.isMainDragging || this.isLeftUpperDragging || this.isLeftLowerDragging) {
            this.isMainDragging = false;
            this.isLeftUpperDragging = false;
            this.isLeftLowerDragging = false;
            document.getElementById("overviewgraph").style.visibility = "visible";
            document.getElementById("graphexportsvg").style.visibility = "visible";
            this.graphoverview.zoomToBoundingBox(true);
        }
    }

    startMainDrag(event) {
        this.isMainDragging = true;
        this.startDraggingPosition = event.clientX;
        document.getElementById("graphexportsvg").style.visibility = "hidden";
        document.getElementById("overviewgraph").style.visibility = "hidden";
        this.addDraggingFunctions();
    }

    startLeftUpperDrag(event) {
        this.isLeftUpperDragging = true;
        this.startDraggingPosition = event.clientY;
        this.addDraggingFunctions();
    }
    
    startLeftLowerDrag(event){
        this.isLeftLowerDragging = true;
        this.startDraggingPosition = event.clientY;
        document.getElementById("overviewgraph").style.visibility = "hidden";
        document.getElementById("graphexportsvg").style.visibility = "hidden";
        this.addDraggingFunctions();
    }

    /**
     * add eventlistener to id=mainontology-graph, because if added directly to html, spinner and number input don't work
     */
    addDraggingFunctions() {
        //mouseup.delegate="endDrag()" 
        document.getElementById("mainontology-graph").addEventListener('mouseup', e => this.endDrag());
        //mousemove.delegate="onDrag($event)" 
        document.getElementById("mainontology-graph").addEventListener('mousemove', e => this.onDrag(e));
        //mouseleave.delegate="endDrag()"
        document.getElementById("mainontology-graph").addEventListener('mouseleave', e => this.endDrag());
    }
    
    onDrag(event) {
        if (this.isMainDragging) {
            let page = document.getElementById("mainontology-graph");
            let searchArea = document.getElementById("menu-section");
            let graphArea = document.getElementById("maingraphpart");

            let leftColWidth = searchArea.clientWidth+4;
            let rightColWidth = graphArea.clientWidth+4;

            let dragbarWidth = 2;
            let move = event.clientX-this.startDraggingPosition
            let total = leftColWidth+dragbarWidth+rightColWidth;
            let cols = [
                ((leftColWidth+move)/total)*100,
                (dragbarWidth/total)*100,
                ((rightColWidth-move)/total)*100
            ];
            let newColDefn = cols.map(c => c.toString() + "%").join(" ");
            page.style.gridTemplateColumns = newColDefn;

            this.startDraggingPosition = event.clientX;
            event.preventDefault()
        } else if(this.isLeftUpperDragging) {
            let menusection = document.getElementById("menu-section");
            let filterSubarea = document.getElementById("item-filtersection");
            let treeSubarea = document.getElementById("item-treesection");
            let overviewSubarea = document.getElementById("item-overview");


            let filterHeight = filterSubarea.clientHeight+1;
            let treeHeight = treeSubarea.clientHeight+1;
            let overviewHeight = overviewSubarea.clientHeight;

            let total = filterHeight+treeHeight+overviewHeight;
            let move = event.clientY-this.startDraggingPosition
            let cols = [
                ((filterHeight+move)/total)*100,
                ((treeHeight-move)/total)*100,
                ((overviewHeight)/total)*100
            ];
            let newColDefn = cols.map(c => c.toString() + "%").join(" ");
            menusection.style.gridTemplateRows = newColDefn;

            this.startDraggingPosition = event.clientY;
            event.preventDefault()

        } else if(this.isLeftLowerDragging) {
            let menusection = document.getElementById("menu-section");
            let filterSubarea = document.getElementById("item-filtersection");
            let treeSubarea = document.getElementById("item-treesection");
            let overviewSubarea = document.getElementById("item-overview");


            let filterHeight = filterSubarea.clientHeight+1;
            let treeHeight = treeSubarea.clientHeight+1;
            let overviewHeight = overviewSubarea.clientHeight;

            let total = filterHeight+treeHeight+overviewHeight;
            let move = event.clientY-this.startDraggingPosition
            let cols = [
                ((filterHeight)/total)*100,
                ((treeHeight+move)/total)*100,
                ((overviewHeight-move)/total)*100
            ];
            let newColDefn = cols.map(c => c.toString() + "%").join(" ");
            menusection.style.gridTemplateRows = newColDefn;

            this.startDraggingPosition = event.clientY;
            event.preventDefault()
        }
    }
}