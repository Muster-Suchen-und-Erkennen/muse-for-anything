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

const boundingBoxBorder: number = 20;

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

class TaxonomyObject {
    name: string;
    href: string;
    namespaceId: string;
    taxonomyId: string;
    description: string | null;
    itemsData: TaxonomyItemApiObject[];
    nodeId: string | number;
}

class TypeNodeTemplate implements DynamicNodeTemplate {

    getLinkHandles(g: Node, grapheditor: GraphEditor): LinkHandle[] {
        return;
    }

    renderInitialTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        this.calculateRect(g, grapheditor, context, false);
    }

    updateTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        this.calculateRect(g, grapheditor, context, true);
    }

    private calculateRect(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>, updated?: boolean) {
        let props = g._groups[0][0].__data__;
        const children = grapheditor.groupingManager.getAllChildrenOf(props.id);
        if (children.size == 0) {
            this.drawRect(g, { x: 0, y: 0, width: 120, height: 20 }, props)
            return;
        }

        const boxes: Rect[] = [];
        children.forEach(childId => {
            const node = grapheditor.getNode(childId);
            const bbox = grapheditor.getNodeBBox(childId);
            boxes.push({
                x: node.x + bbox.x,
                y: node.y + bbox.y,
                width: bbox.width,
                height: bbox.height,
            });
        });

        const minBox = calculateMinBoundingRect(boxes);

        this.drawRect(g, minBox, props);
    }

    private drawRect(g: any, minBox: any, props: any) {
        g.selectAll("*").remove();
        g.append("rect")
            .attr("width", minBox.width + boundingBoxBorder * 2)
            .attr("height", minBox.height + boundingBoxBorder * 2)
            .attr("class", "type-group")
            .attr("rx", 5);
        g.append("text")
            .attr("x", 5)
            .attr("y", 15)
            .attr("class", "title")
            .attr("width", minBox.width + boundingBoxBorder * 2 - 5)
            .attr('data-content', 'title');
    }
}

function calculateMinBoundingRect(boxes: Rect[]): Rect {
    const minBox = calculateBoundingRect(...boxes);
    minBox.width = Math.max(160, minBox.width);
    minBox.height = Math.max(80, minBox.height);
    return minBox;
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

    public icon: string;
    public children: DataItemModel[];
    public expanded: boolean;
    public visible: boolean;
    @observable() isSelected: boolean;
    private graph: GraphEditor;

    constructor(id: string, name: string, href: string, description: string, itemType: DataItemTypeEnum, graph: GraphEditor, isVisible = true, taxonomyChildRelations = []) {
        this.id = id;
        this.name = name;
        this.href = href;
        this.description = description;
        this.itemType = itemType;
        this.expanded = false;
        this.visible = isVisible;
        this.graph = graph;
        this.children = [];
        this.taxonomyParentRelations = taxonomyChildRelations;
    }

    hasChildren() {
        return this.children.length > 0;
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

    isSelectedChanged(newValue, oldValue) {
        console.log(this.children)
        if (newValue === true) {
            this.graph.selectNode(this.id);
        } else {
            this.graph.deselectNode(this.id);
        }
        this.graph.updateHighlights();
    }


    addChild(id: string, name: string, href: string, description: string, itemType: DataItemTypeEnum, childHrefs?: string[]) {
        this.children.push(new DataItemModel(id, name, href, description, itemType, this.graph, false, childHrefs));
        this.icon = "arrow-right";
        this.expanded = false;
    }
}

class TaxonomyNodeTemplate implements DynamicNodeTemplate {

    getLinkHandles(g: any, grapheditor: GraphEditor): LinkHandle[] {
        return;
    }

    renderInitialTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        this.calculateRect(g, grapheditor, context, false);
    }

    updateTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        this.calculateRect(g, grapheditor, context, true);
    }

    private calculateRect(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>, updated?: boolean) {
        let props = g._groups[0][0].__data__;
        const children = grapheditor.groupingManager.getAllChildrenOf(props.id);

        if (children.size == 0) {
            this.drawRect(g, { x: 0, y: 0, width: 120, height: 20 }, props, false)
            return;
        }

        const boxes: Rect[] = [];
        children.forEach(childId => {
            const node = grapheditor.getNode(childId);
            const bbox = grapheditor.getNodeBBox(childId);

            boxes.push({
                x: node.x + bbox.x,
                y: node.y + bbox.y,
                width: bbox.width,
                height: bbox.height,
            });
        });

        let minBox = calculateMinBoundingRect(boxes);

        this.drawRect(g, minBox, props, true);
    }

    private drawRect(g: any, minBox: any, props: any, childsVisible: boolean) {
        g.selectAll("*").remove();
        g.append("rect")
            .attr("width", minBox.width + boundingBoxBorder * 2)
            .attr("height", minBox.height + boundingBoxBorder * 2)
            .attr("class", "taxonomy-group")
            .attr("data-click", "node")
            .attr("rx", 5);
        g.append("text")
            .attr("x", 5)
            .attr("y", 15)
            .attr("class", "title")
            .attr("width", minBox.width + boundingBoxBorder * 2 - 5)
            .attr("data-click", "header")
            .attr('data-content', 'title');

        // add + or - to node for collapsing details or not
        let collapseIconElement = g.append("g")
            .attr("transform", "translate(5,20)")
            .attr("data-click", "expandNode").attr("fill", "white").attr("fill-rule", "evenodd").attr("stroke", "currentColor").attr("stroke-linecap", "round").attr("stroke-linejoin", "round")
        collapseIconElement.append("path").attr("d", "m12.5 10.5v-8c0-1.1045695-.8954305-2-2-2h-8c-1.1045695 0-2 .8954305-2 2v8c0 1.1045695.8954305 2 2 2h8c1.1045695 0 2-.8954305 2-2z")
        collapseIconElement.append("path").attr("d", "m6.5 3.5v6").attr("transform", "matrix(0 1 -1 0 13 0)")

        if (!childsVisible) collapseIconElement.append("path").attr("d", "m6.5 3.5v6.056")
    }
}

class OverviewGraphNode implements DynamicNodeTemplate {

    getLinkHandles(g: any, grapheditor: GraphEditor): LinkHandle[] {
        return;
    }

    renderInitialTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        let props = g._groups[0][0].__data__;
        g.selectAll("*").remove();
        this.drawRect(g, props);
    }

    updateTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        let props = g._groups[0][0].__data__;
        g.selectAll("*").remove();
        this.drawRect(g, props);
    }

    private drawRect(g: any, props: any) {
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
        repositionGroupNode(group, groupNode, graphEditor);
    }

    onNodeMoveEnd(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor) {
        repositionGroupNode(group, groupNode, graphEditor);
    }
}

class TypeGroupBehaviour implements GroupBehaviour {
    moveChildrenAlongGoup = true;
    captureDraggedNodes = false;
    allowFreePositioning = true;
    allowDraggedNodesLeavingGroup = false;

    afterNodeJoinedGroup(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor, atPosition?: Point) {
        repositionGroupNode(group, groupNode, graphEditor);
    }

    afterNodeLeftGroup(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor) {
        //repositionGroupNode(group, groupNode, graphEditor);
    }

    onNodeMoveStart(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor) {
        repositionGroupNode(group, groupNode, graphEditor);
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

    // set config moveChildrenAlongGoup to false, to position group node around children, and set config back
    const tempConfig = graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup;
    graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup = false;
    graphEditor.moveNode(groupNode.id, minBox.x - boundingBoxBorder, minBox.y - boundingBoxBorder, false);
    graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup = tempConfig;

    graphEditor.completeRender();
}

@autoinject
export class OntologyGraph {
    @bindable isLoading = 0;
    @bindable apiLink;
    @bindable ignoreCache = false;
    @bindable maximizeMenu = false;

    totalNodesToAdd = 0;
    totalNodesAdded = 0;

    maximized: boolean = false;
    isAllowedToShowGraph: boolean = false;
    speed: number = 10; // pixels to move the nodes in the graph on interaction

    @child("network-graph.maingraph") graph: GraphEditor;
    @child("div.maindiv") maindiv: any;
    @observable graphoverview: GraphEditor;

    @observable() searchtext: String = "";
    @observable() selectedNode: Node;
    @observable() typeChildsToShow: number = 3;

    missingParentConnection: Array<{ parent: number | string, child: number | string, joinTree: boolean }> = [];

    @observable() dataItems: Array<DataItemModel> = [];

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

        bindingEngine.collectionObserver(this.dataItems)
            .subscribe(this.dataItemsChanged.bind(this));
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

    dataItemsChanged(newValue) {
    }

    apiLinkChanged(newValue: ApiLink, oldValue) {
        if (newValue == null) {
            return;
        }
        this.loadData(this.apiLink, this.ignoreCache);
    }

    maindivChanged(newValue: any, oldValue) {
        // need div, to get access to the graph overview part
        if (newValue == null) {
            return;
        }

        if (newValue.getElementsByClassName("graphoverview").length > 0) {
            //this.graphoverview = newValue.getElementsByClassName("graphoverview")[0]
        } else {
            throw new Error("No graphoverview element in DOM found")
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
    }

    graphoverviewChanged(newGraph: GraphEditor, oldGraph) {
        if (newGraph == null) {
            return;
        }
        newGraph.dynamicTemplateRegistry.addDynamicTemplate('overview-node-template', new OverviewGraphNode);
        newGraph.dynamicTemplateRegistry.addDynamicTemplate('type-group-node-template', new TypeNodeTemplate);
        newGraph.dynamicTemplateRegistry.addDynamicTemplate('taxonomy-group-node-template', new TaxonomyNodeTemplate);
    }

    searchtextChanged(newText: string, old: string) {
        if (this.graph == null) {
            return;
        }
        if (newText == "") {
            this.graph.changeSelected(null);
        } else {
            this.graph.nodeList.forEach(node => {
                if (node.title.includes(newText)) {
                    this.graph.selectNode(node.id);
                } else {
                    this.graph.deselectNode(node.id);
                }
            });
        }

        this.recursiveListSearch(this.dataItems, newText);

        this.graph.updateHighlights();
    }

    typeChildsToShowChanged(newValue: number, oldValue: number) {
        if (oldValue == newValue || this.graph == null) return;
        this.dataItems?.filter(p => p.itemType == DataItemTypeEnum.TypeItem).forEach(parent => {
            if (oldValue > newValue) {
                //delete items
                let childs = parent.children;
                let counter = 0;
                childs.forEach(childItem => {
                    if (counter < newValue) {

                    } else if (this.graph.nodeList.some(p => p.id == childItem.id)) {
                        this.graph.groupingManager.removeNodeFromGroup(parent.id, childItem.id);
                        this.graph.removeNode(childItem.id);
                    }
                    counter++;
                })
            } else if (newValue > oldValue && this.graph.nodeList.some(p => p.id == parent.id)) {
                //add items
                let childs: Set<string> = this.graph.groupingManager.getAllChildrenOf(parent.id);

                if (childs.size < Math.min(parent.children.length, newValue)) {
                    for (let i = childs.size; i < Math.min(parent.children.length, newValue); i++) {
                        if (childs.size == 0) {
                            this.addItemToType(parent.children[i], { x: parent.node.x, y: parent.node.y }, parent);
                        } else {
                            let { width, height } = this.getSizeOfStaticTemplateNode(parent.children[i - 1].node.type);
                            this.addItemToType(parent.children[i], { x: parent.children[i - 1].node.x - Math.floor(width / 2), y: parent.children[i - 1].node.y + Math.floor(height / 2) }, parent);
                        }
                    }
                }

            }
        });
        this.graph.completeRender();
        this.addChildnodesToParents();
        this.updateHiddenLinks();
        this.graph.completeRender();
    }

    recursiveListSearch(items: DataItemModel[], searchText: string) {
        items.forEach(item => {
            if (item.name.includes(searchText) && searchText != "") {
                item.isSelected = true;
            }
            else {
                item.isSelected = false;
            }
            this.recursiveListSearch(item.children, searchText)
        })
    }

    private loadData(apiLink: ApiLink, ignoreCache: boolean) {
        console.log("Start loading data")
        this.loadDataTaxonomy(apiLink.href + "taxonomies/", this.ignoreCache);
        this.loadDataTypes(apiLink.href + "types/", this.ignoreCache);
    }

    private loadDataTypes(linkNamespace: string, ignoreCache: boolean) {
        const promises = [];
        let typesRootLink: ApiLink = { href: linkNamespace, rel: null, resourceType: null };
        promises.push(this.api.getByApiLink<TypeApiObject>(typesRootLink, ignoreCache).then(apiResponse => {
            apiResponse.links.forEach(link => {
                if (link.rel.includes("next")) {
                    this.loadDataTypes(link.href, this.ignoreCache);
                }
            })
            // for each type in namespace
            apiResponse.data.items?.forEach(element => {
                // load each type of the namespace
                promises.push(this.api.getByApiLink<TypeItemApiObject>(element, ignoreCache).then(apiResponse => {
                    let data = apiResponse.data;
                    let nodeID = this.createUniqueId(data.self.href);
                    this.dataItems.push(new DataItemModel(nodeID, data.name, data.self.href, data.schema.description, DataItemTypeEnum.TypeItem, this.graph));
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
                        //typeEnum == DataItemTypeEnum.TaxonomyProperty ||

                        let childID = this.createUniqueId(typeHref)
                        this.dataItems.find(p => p.id == nodeID).addChild(childID, typeElement, typeHref, "tbd", typeEnum);
                    }
                }));
            });
        }));
        Promise.all(promises).then(() => {
            console.log("done with all type data")
            //this.finishDataLoading();
        });
    }


    private loadDataTaxonomy(linkNamespace: string, ignoreCache: boolean) {
        const promises = [];
        let newlink: ApiLink = { href: linkNamespace, rel: null, resourceType: null };
        promises.push(this.api.getByApiLink<TaxonomyApiObject>(newlink, ignoreCache).then(apiResponse => {
            apiResponse.links.forEach(link => {
                if (link.rel.includes("next")) {
                    this.loadDataTaxonomy(link.href, this.ignoreCache);
                }
            })
            // for each taxonomy in namespace
            apiResponse.data.items.forEach(element => {
                promises.push(this.api.getByApiLink<TaxonomyApiObject>(element, ignoreCache).then(apiResponse => {
                    let nodeID = this.createUniqueId(apiResponse.data.self.href);
                    this.dataItems.push(new DataItemModel(nodeID, apiResponse.data.name, apiResponse.data.self.href, apiResponse.data.description, DataItemTypeEnum.TaxonomyItem, this.graph))
                    apiResponse.data.items.forEach(element => {
                        promises.push(this.api.getByApiLink<TaxonomyItemApiObject>(element, ignoreCache).then(apiResponse => {

                            //load taxonomy relations
                            let parentItemHrefs: string[] = [];
                            apiResponse.data.children.forEach(childElement => {
                                promises.push(this.api.getByApiLink<TaxonomyItemRelationApiObject>(childElement, ignoreCache).then(apiResponses => {
                                    parentItemHrefs.push(apiResponses.data.targetItem.href)
                                }));
                            });
                            this.dataItems.find(p => p.id == nodeID).addChild(this.createUniqueId(apiResponse.data.self.href), apiResponse.data.name, apiResponse.data.self.href, apiResponse.data.description, DataItemTypeEnum.TaxonomyItemProperty, parentItemHrefs);

                        }));
                    });

                }));
            });
        }));
        Promise.all(promises).then(() => {
            console.log("done with all tax data")
            //this.finishDataLoading();
        });
    }


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

    private sortList(items: DataItemModel[]) {
        items.sort(function(a, b) {
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

    private async renderGraph() {
        this.sortList(this.dataItems);
        
        let startTime = Date.now();
        if (this.graph == null) {
            return;
        }

        await this.dataItems.forEach(element => {
            if (element.itemType == DataItemTypeEnum.TypeItem) {
                let pos = { x: Math.floor(Math.random() * 1000), y: Math.floor(Math.random() * 1000) };
                this.addTypeItem(element, pos);
            }
        });

        await this.dataItems.forEach((element) => {
            if (element.itemType == DataItemTypeEnum.TaxonomyItem) {
                let pos = { x: Math.floor(Math.random() * 1000), y: Math.floor(Math.random() * 1000) };
                this.addTaxonomyItem(element, pos);
            }
        });

        await this.graph.completeRender();

        await this.addChildnodesToParents();

        await this.updateHiddenLinks();

        await this.graph.completeRender();

        await this.graph?.zoomToBoundingBox();

        this.isLoading = 2;
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
                                    scale: 0.8,
                                    relativeRotation: 0,
                                }
                            }

                            if (!this.graph.edgeList.some(p => p.source == source && p.target == parent.id) &&
                                this.graph.nodeList.some(p => p.id == path.source) &&
                                this.graph.nodeList.some(p => p.id == path.target)) {
                                this.graph.addEdge(path, false)
                                this.graphoverview?.addEdge(path, false)
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

    // check if a string is a number
    private isNumber(value: string | number): boolean {
        return ((value != null) &&
            (value !== '') &&
            !isNaN(Number(value.toString())));
    }

    private getTaxonomyHref(namespaceId: number, taxonomyID: number): string {
        return "http://localhost:5000/api/v1/namespaces/" + namespaceId + "/taxonomies/" + taxonomyID + "/";
    }

    private getTypeHref(namespaceId: number, typeID: number): string {
        return "http://localhost:5000/api/v1/namespaces/" + namespaceId + "/types/" + typeID + "/";
    }

    private addTypeItem(parentItem: DataItemModel, parentPosition: { x, y }): { x, y } {
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
        let nodeBox: { x, y } = { x: parentBox.x, y: parentBox.y };
        let counter = 0;
        parentItem.children.forEach(childItem => {
            if (counter >= this.typeChildsToShow) return;
            counter++;
            nodeBox = this.addItemToType(childItem, nodeBox, parentItem);

        });
        return this.getLeftBottomPointOfItem(parentItem.node);
    }

    private addItemToType(childItem: DataItemModel, nodeBox: { x, y }, parentItem: DataItemModel): { x, y } {
        if (childItem.itemType == DataItemTypeEnum.TaxonomyProperty) {
            nodeBox = this.addNodeToGraph({ id: childItem.id, title: childItem.name, type: "taxonomy-link-item", x: nodeBox.x, y: nodeBox.y, typedescription: "Taxonomy-Ref" }, false);
        } else if (childItem.itemType == DataItemTypeEnum.TypeProperty) {
            nodeBox = this.addNodeToGraph({ id: childItem.id, title: childItem.name, type: "type-link-item", x: nodeBox.x, y: nodeBox.y, typedescription: "Type-Ref" }, false);
        } else if (childItem.itemType == DataItemTypeEnum.EnumProperty ||
            childItem.itemType == DataItemTypeEnum.BooleanProperty ||
            childItem.itemType == DataItemTypeEnum.IntegerProperty ||
            childItem.itemType == DataItemTypeEnum.NumberProperty ||
            childItem.itemType == DataItemTypeEnum.StringProperty ||
            childItem.itemType == DataItemTypeEnum.Undefined) {
            nodeBox = this.addNodeToGraph({ id: childItem.id, title: childItem.name, type: "taxonomy-item", x: nodeBox.x, y: nodeBox.y, typedescription: childItem.itemType }, false);
        } else {
            console.log("fuckof", childItem)
        }
        this.missingParentConnection.push({ parent: parentItem.id, child: childItem.id, joinTree: false })
        return nodeBox;
    }

    private addTaxonomyItem(parentItem: DataItemModel, parentPosition: { x, y }): { x, y } {
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

        let childElements: Array<{ href: string, id: string }> = []
        taxonomyParent.children.forEach(childElement => {
            this.addNodeToGraph({ id: childElement.id, title: childElement.name, type: 'taxonomy-item', x: parentBox.x + (Math.floor(childElements.length / 2)) * (Number(taxonomyItemSize.width) + 10), y: parentBox.y + (childElements.length % 2) * (Number(taxonomyItemSize.height) + 10) }, false);
            childElements.push({ href: childElement.href, id: childElement.id });
            this.missingParentConnection.push({ parent: taxonomyParent.id, child: childElement.id, joinTree: false })
        });

        taxonomyParent.children.forEach(source => {
            source.taxonomyParentRelations.forEach(target => {

                this.addEdgeToTaxonomy(source.id, taxonomyParent.children.find(f => f.href == target).id);
            })
        })
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
                scale: 0.8,
                relativeRotation: 0,
            }
        }
        this.graph.addEdge(path, false)
    }

    private createUniqueId(nodeID: string): string {
        nodeID = String(nodeID).replace(RegExp(/\/\/|\/|:| /g), "")
        // add some random number (unix time stamp) to the id, no make it unique
        let nodeIdOrig = nodeID;
        nodeID = nodeIdOrig + "-" + Math.floor(Math.random() * 100 * Date.now())

        while (this.dataItems.some(element => element.id == nodeID)) {
            nodeID = nodeIdOrig + "-" + Math.floor(Math.random() * 100 * Date.now())
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

        this.graph?.addNode(node, false);
        this.graphoverview?.addNode(node, false);

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
        let width = this.graph.staticTemplateRegistry.getNodeTemplate(nodeType)._groups[0][0].getElementsByTagName("rect")[0].getAttribute("width");
        let height = this.graph.staticTemplateRegistry.getNodeTemplate(nodeType)._groups[0][0].getElementsByTagName("rect")[0].getAttribute("height");
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
        console.log("Click event", event)

        if (node.dynamicTemplate === "taxonomy-group-node-template" && event.detail.key == "expandNode") {
            if (this.graph.groupingManager.getAllChildrenOf(node.id).size > 0) {
                this.graph.groupingManager.getAllChildrenOf(node.id).forEach(child => {
                    this.graph.groupingManager.removeNodeFromGroup(node.id, child)
                    this.graph.removeNode(child, true);
                    this.graphoverview?.removeNode(child, true);
                })
            }
            else {
                this.addItemsToTaxonomy(this.dataItems.find(t => t.id == node.id), this.getLeftBottomPointOfItem(node));
                this.graph.completeRender();
                this.addChildnodesToParents();
            }
        }

        if (event.detail.key == "header") {
            this.selectedNode = node;
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
    }

    private onNodeAdd(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node }>) {
        let currentView = this.graph.currentViewWindow;
        this.graphoverview?.removeNode(42424242424242424242424242424242421, false);
        this.graphoverview?.addNode({ id: 42424242424242424242424242424242421, class: "invisible-rect", dynamicTemplate: 'overview-node-template', x: currentView.x, y: currentView.y, width: currentView.width, height: currentView.height }, false);
    }

    private onZoomChange(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node }>) {
        this.renderMainViewPositionInOverviewGraph();
    }

    private renderMainViewPositionInOverviewGraph() {
        let currentView = this.graph.currentViewWindow;
        this.graphoverview?.removeNode(4242424242424242424242424242424242, false);
        this.graphoverview?.addNode({ id: 4242424242424242424242424242424242, class: "position-rect", dynamicTemplate: 'overview-node-template', x: currentView.x, y: currentView.y, width: currentView.width, height: currentView.height }, true);
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
    }

    // function called by buttons from the front-end, to interact with the graph
    private toggleMenu() {
        this.maximizeMenu = !this.maximizeMenu;
    }

    // function called by buttons from the front-end, to interact with the graph
    private resetLayout() {
        this.graph?.zoomToBoundingBox(true);
    }

    // function called by buttons from the front-end, to interact with the graph
    private moveGraph(direction: String) {
        let dirX = this.speed;
        let dirY = this.speed;

        let div = -80;
        let currentView = this.graph.currentViewWindow;
        if (direction == 'down') {
            currentView.y = currentView.y - dirY;
        } else if (direction == 'right') {
            currentView.x = currentView.x - dirX;
        } else if (direction == 'left') {
            currentView.x = currentView.x + dirX;
        } else if (direction == 'up') {
            currentView.y = currentView.y + dirY;
        }
        currentView.x = currentView.x - div;
        currentView.y = currentView.y - div;
        currentView.height = currentView.height + 2 * div;
        currentView.width = currentView.width + 2 * div;

        /*this.graph.nodeList.forEach(node => {            
            this.graph.moveNode(node.id, node.x+dirX, node.y+dirY, false);
        })*/


        this.graph.zoomToBox(currentView);

        this.graph.completeRender();
    }
}