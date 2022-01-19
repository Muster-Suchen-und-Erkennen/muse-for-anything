import { edgeId } from "@ustutt/grapheditor-webcomponent/lib/edge";
import GraphEditor from "@ustutt/grapheditor-webcomponent/lib/grapheditor";
import { Node } from "@ustutt/grapheditor-webcomponent/lib/node";
import { Rect } from "@ustutt/grapheditor-webcomponent/lib/util";
import { EventAggregator, Subscription } from "aurelia-event-aggregator";
import { autoinject, bindable, child, observable, TaskQueue } from "aurelia-framework";
import { NAV_LINKS_CHANNEL } from "resources/events";
import { ApiLink } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";
import { NavigationLinksService, NavLinks } from "services/navigation-links";
import { TaxonomyGroupBehaviour, TypeGroupBehaviour } from "./ontology-graph-util/group-behaviours";
import { calculateNodePositionsd3, calculateNodePositionsNgraph } from "./ontology-graph-util/layouts";
import { OverviewGraphNode, TaxonomyNodeTemplate, TypeNodeTemplate } from "./ontology-graph-util/node-templates";
import { addTaxonomyChildrenToDataItem, addTypeChildrenToDataItem, CHILD_ITEM_TYPE_SET, compareDataItems, DataItemModel, DataItemTypeEnum, GROUP_DATA_ITEM_TYPE_SET, loadTaxonomies, loadTypes, mapDataItemToGraphNode, taxonomyApiResponseToDataItemModel, TAXONOMY_DATA_ITEM_TYPE_SET, typeApiResponseToDataItemModel, TYPE_DATA_ITEM_TYPE_SET } from "./ontology-graph-util/util";



@autoinject
export class OntologyGraph {
    @bindable isLoading = true;
    @bindable isRendered = false;
    @bindable apiLink;
    @bindable ignoreCache = false;
    @bindable maximizeMenu = false;

    @observable() searchtext: string = "";
    @observable() keepSearchResultsInFocus: boolean = false;

    @observable() typeChildsToShow: number = 3;
    @observable() taxonomyLevelsToShow: number = 0;

    @observable() showTaxonomies: boolean = true;
    @observable() showTypes: boolean = true;
    @observable() showSelectedItems: boolean = false;
    @observable() showElementsWithoutAnEdge: boolean = false;

    @observable() selectedNode: DataItemModel;

    @observable() selectedLayoutAlgorithmId: number = 1;
    @observable() distanceBetweenElements: number = 100;

    @observable() currentEdgeStyleBold: boolean = true;

    @observable graph: GraphEditor;
    @observable graphoverview: GraphEditor;
    @child("div#mainontology-graph") maindiv: any;

    private layoutAlgorithms = [
        { id: 0, name: "ngraph.forcedirected" },
        { id: 1, name: "d3-force" },
    ];

    private totalTypes = 0;
    private totalTaxonomies = 0;
    private taxonomyChildItems: number;

    private maximized: boolean = false;
    private isAllowedToShowGraph: boolean = false;

    private missingParentConnection: Array<{ parent: number | string, child: number | string, joinTree: boolean }> = [];

    dataItems: DataItemModel[] = [];
    dataItemsMap: Map<string, DataItemModel> = new Map();
    dataItemChildrenMap: Map<string, Set<string>> = new Map();
    dataItemsWithEdges: Set<string> = new Set();

    currentSearchMatches: Set<string> | null = null;
    maskSearchMisses: boolean = false;
    searchHasFocus: boolean = false;

    private api: BaseApiService;
    private navService: NavigationLinksService;
    private events: EventAggregator;
    private queue: TaskQueue;
    private subscription: Subscription;

    constructor(baseApi: BaseApiService, navService: NavigationLinksService, events: EventAggregator, queue: TaskQueue) {
        this.api = baseApi;
        this.navService = navService;
        this.checkNavigationLinks();
        this.events = events;
        this.queue = queue;
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
        if (newValue.getElementsByClassName("graphoverview").length > 0) {
            this.graphoverview = newValue.getElementsByClassName("graphoverview")[0];
        } else {
            throw new Error("No graphoverview element in DOM found");
        }
        if (newValue.getElementsByClassName("maingraph").length > 0) {
            this.graph = newValue.getElementsByClassName("maingraph")[0];
        } else {
            throw new Error("No graph element in DOM found");
        }
    }

    private setNodeClass = (className: string, node: Node): boolean => { // lambda to keep this binding intact
        if (className === node.type) {
            return true;
        }
        if (className === "group-node" && node.isGroupNode) {
            return true;
        }
        if (className === "child-node" && !node.isGroupNode) {
            return true;
        }
        if (className === "search-match" && this.currentSearchMatches != null) {
            return this.currentSearchMatches.has(node.id as string);
        }
        if (className === "ghost-node" && this.currentSearchMatches != null && this.maskSearchMisses) {
            return !this.currentSearchMatches.has(node.id as string);
        }
        return false;
    };

    private setEdgeClass = (className, edge, sourceNode, targetNode) => { // lambda to keep this binding intact
        if (className === "big-edge") {
            return this.currentEdgeStyleBold;
        }
        if (className === "ghost-edge" && this.currentSearchMatches != null && this.maskSearchMisses) {
            // both source and target cannot be search matches for the edge to be a ghost edge
            return (!this.currentSearchMatches.has(edge.source as string)) && (!this.currentSearchMatches.has(edge.target as string));
        }
        return false;
    };

    graphChanged(newGraph: GraphEditor): void {
        if (newGraph == null) {
            return;
        }
        newGraph.addEventListener("nodeclick", (event) => this.onNodeClick(event as any));
        newGraph.addEventListener("backgroundclick", (event) => this.onBackgroundClick(event as any));
        newGraph.addEventListener("selection", (event) => this.onSelectionChanged(event as any));
        newGraph.addEventListener("zoomchange", (event) => this.onZoomChange(event as any));
        newGraph.addEventListener("nodepositionchange", (event) => this.onNodePositionChange(event as any));
        newGraph.addEventListener("nodedragend", (event) => this.onNodeDragEnd(event as any));

        newGraph.dynamicTemplateRegistry.addDynamicTemplate("type-group-node-template", new TypeNodeTemplate);
        newGraph.dynamicTemplateRegistry.addDynamicTemplate("taxonomy-group-node-template", new TaxonomyNodeTemplate);

        newGraph.setNodeClass = this.setNodeClass;
        newGraph.setEdgeClass = this.setEdgeClass;
    }

    graphoverviewChanged(newGraph: GraphEditor): void {
        if (newGraph == null) {
            return;
        }
        newGraph.dynamicTemplateRegistry.addDynamicTemplate("overview-node-template", new OverviewGraphNode);
        newGraph.dynamicTemplateRegistry.addDynamicTemplate("type-group-node-template", new TypeNodeTemplate);
        newGraph.dynamicTemplateRegistry.addDynamicTemplate("taxonomy-group-node-template", new TaxonomyNodeTemplate);

        newGraph.setNodeClass = this.setNodeClass;
        newGraph.setEdgeClass = this.setEdgeClass;

        newGraph.addEventListener("svginitialized", () => {
            newGraph.getSVG()
                ?.select("g.zoom-group")
                ?.append("rect")
                ?.classed("view-window", true);
        });
    }

    selectedLayoutAlgorithmIdChanged(): void {
        this.updateLayout();
    }

    distanceBetweenElementsChanged(): void {
        this.updateLayout();
    }

    searchtextChanged(newText: string): void {
        this.searchHasFocus = true;
        this.maskSearchMisses = true;
        this.updateSearchFilter(newText);
    }

    private updateSearchFilter(searchString: string) {
        if (this.graph == null) {
            return;
        }

        const indirectMatches = new Set<string>();
        const searchMatches = new Set<string>();

        const searchText = searchString.toLowerCase().trim();

        const addParentsAsIndirectMatch = (item: DataItemModel) => {
            item.parentIds.forEach(parentId => {
                indirectMatches.add(parentId);
                const parent = this.dataItemsMap.get(parentId);
                if (parent != null) {
                    addParentsAsIndirectMatch(parent);
                }
            });
        };

        this.dataItemsMap.forEach(item => {
            if (searchText === "") { // match everything on empty search
                searchMatches.add(item.id);
                item.isSearchResult = false;
                return;
            }
            // find search results
            if (item.name.toLowerCase().includes(searchText)) {
                searchMatches.add(item.id);
                // deal with parents of search matches
                addParentsAsIndirectMatch(item);
            }
        });

        this.dataItemsMap.forEach(item => {
            // apply search results
            if (item.expanded && this.maskSearchMisses && !indirectMatches.has(item.id)) {
                item.toggleNode();
            }
            item.visible = searchText === "" || !this.maskSearchMisses || searchMatches.has(item.id) || indirectMatches.has(item.id);
        });

        this.currentSearchMatches = searchText !== "" ? searchMatches : null;

        this.graph?.updateNodeClasses();
        this.graph?.updateEdgeGroupClasses();
        this.graphoverview?.updateNodeClasses();

    }

    keepSearchResultsInFocusChanged(newValue: boolean): void {
        if (this.searchHasFocus) {
            this.maskSearchMisses = true;
            return; // searchMisses should already be hidden
        }
        this.maskSearchMisses = newValue;
        this.updateSearchFilter(this.searchtext);
    }

    /**
     * Focus has entered the search field. Apply search filter.
     */
    searchtextFocusEnter() {
        this.searchHasFocus = true;
        this.maskSearchMisses = true;
        this.updateSearchFilter(this.searchtext);
    }

    /**
     * Focus has left the search field. Remove search filter if keepSearchResultsInFocus === false
     */
    searchtextFocusLeft(event) {
        this.searchHasFocus = false;
        if (this.keepSearchResultsInFocus) {
            return; // do nothing if search results should keep being in focus
        }
        this.maskSearchMisses = false;
        this.updateSearchFilter(this.searchtext);
    }

    typeChildsToShowChanged(newValue: number): void {
        if (!this.isRendered) {
            return;
        }
        this.renderGraph();
    }

    taxonomyLevelsToShowChanged(newValue: number): void {
        if (!this.isRendered) {
            return;
        }
        this.renderGraph();
    }

    showTaxonomiesChanged(value: boolean): void {
        if (!this.isRendered) {
            return;
        }
        this.renderGraph();
    }

    showTypesChanged(value: boolean): void {
        if (!this.isRendered) {
            return;
        }
        this.renderGraph();
    }

    showElementsWithoutAnEdgeChanged(value: boolean): void {
        if (!this.isRendered) {
            return;
        }
        this.renderGraph();
    }

    showSelectedItemsChanged(value: boolean) {
        if (!this.isRendered) {
            return;
        }
        this.renderGraph();
    }

    /**
     * load the data from the server, links are given by the navigation service
     * @param ignoreCache
     */
    private loadData(ignoreCache: boolean) {
        // TODO load data in batches!
        const promises: Array<Promise<DataItemModel[]>> = [];
        if (this.navService.getCurrentNavLinks().nav.some(link => link.apiLink.resourceType == "ont-type")) {
            const firstTypePage = this.navService.getCurrentNavLinks().nav.find(link => link.apiLink.resourceType === "ont-type").apiLink;
            const typesPromise = loadTypes(this.api, firstTypePage, this.ignoreCache) // load types
                .then(results => {
                    this.totalTypes = results.totalTypes;
                    return Promise.all(results.typeApiResponses); // wait for all type promises
                })
                .then(apiResponses => {
                    // map api responses to DataItemModels
                    return Promise.all(apiResponses.map(response => {
                        const dataModel = typeApiResponseToDataItemModel(response, this.graph);
                        return addTypeChildrenToDataItem(response, dataModel, this.api).then(() => dataModel);
                    }));
                });
            promises.push(typesPromise);
        }
        if (this.navService.getCurrentNavLinks().nav.some(link => link.apiLink.resourceType == "ont-taxonomy")) {
            const firstTaxonomyPage = this.navService.getCurrentNavLinks().nav.find(link => link.apiLink.resourceType === "ont-taxonomy").apiLink;
            const taxonomyPromise = loadTaxonomies(this.api, firstTaxonomyPage, this.ignoreCache) // load taxonomies
                .then(results => {
                    this.totalTaxonomies = results.totalTaxonomies;
                    return Promise.all(results.taxonomyApiResponses); // wait for all type promises
                })
                .then(apiResponses => {
                    // map api responses to DataItemModels
                    return Promise.all(apiResponses.map(response => {
                        const dataModel = taxonomyApiResponseToDataItemModel(response, this.graph);
                        return addTaxonomyChildrenToDataItem(response, dataModel, this.graph, this.api).then(() => dataModel);
                    }));
                });
            promises.push(taxonomyPromise);
        }

        // marging all promises
        if (promises.length > 0) {
            Promise.all(promises)
                .then((dataItemLists) => {
                    const dataItems: DataItemModel[] = [].concat(...dataItemLists);
                    dataItems.sort(compareDataItems);
                    const dataItemsMap = new Map<string, DataItemModel>();
                    const dataItemChildrenMap = new Map<string, Set<string>>();
                    const dataItemsWithEdges = new Set<string>();

                    let z = 0;

                    const addItems = (item: DataItemModel, index, depth = 0) => {
                        item.node = mapDataItemToGraphNode(item); // create node objects for data items
                        if (item.node.z == null) {
                            // only set and increase z for new nodes that have no z value
                            item.node.z = z;
                            z++;
                        }
                        if (item.node.index == null) {
                            item.node.index = index;
                        }
                        if (item.node.depth == null) {
                            item.node.depth = depth;
                        }
                        dataItemsMap.set(item.id, item); // sort data items in a map for fast access

                        // gather a set of child ids for all root ids
                        if (item.rootId) {
                            if (!dataItemChildrenMap.has(item.rootId)) {
                                dataItemChildrenMap.set(item.rootId, new Set([item.id]));
                            } else {
                                dataItemChildrenMap.get(item.rootId).add(item.id);
                            }
                        }

                        // check edges to fill out dataItemsWithEdges
                        if (item.referenceTargetId != null && item.rootId != null) {
                            dataItemsWithEdges.add(item.rootId); // only group roots are considered edge targets
                            dataItemsWithEdges.add(item.referenceTargetId); // reference target can only point to group roots
                        }

                        // handle children
                        if (item.hasChildren()) {
                            item.children.sort(compareDataItems); // also sort children
                            item.children.forEach((child, index) => addItems(child, index, depth + 1));
                        }
                    };
                    dataItems.forEach((item, index) => addItems(item, index));
                    this.dataItems = dataItems;
                    this.dataItemsMap = dataItemsMap;
                    this.dataItemsWithEdges = dataItemsWithEdges;
                    this.isLoading = false;
                    this.prepareGroups();
                    this.renderGraph(true);
                });
        }
    }

    private prepareGroups() {
        const gm = this.graph.groupingManager;
        gm.clearAllGroups();
        this.dataItemsMap.forEach((item) => {
            if (GROUP_DATA_ITEM_TYPE_SET.has(item.itemType)) {
                if (item.itemType === DataItemTypeEnum.TypeItem && !item.abstract) {
                    gm.markAsTreeRoot(item.id);
                    gm.setGroupBehaviourOf(item.id, new TypeGroupBehaviour());
                }
                if (item.itemType === DataItemTypeEnum.TaxonomyItem) {
                    gm.markAsTreeRoot(item.id);
                    gm.setGroupBehaviourOf(item.id, new TaxonomyGroupBehaviour());
                }
                return;
            }
        });
    }

    private itemTypeIsVisible(item: DataItemModel): boolean {
        if (TYPE_DATA_ITEM_TYPE_SET.has(item.itemType)) {
            if (this.showTypes && !item.abstract) { // TODO better filter for abstract types...
                if (item.rootId == null || this.dataItemsMap.get(item.rootId)?.isVisibleInGraph) {
                    return item.isVisibleInGraph;
                }
            }
            return false;
        }
        if (TAXONOMY_DATA_ITEM_TYPE_SET.has(item.itemType)) {
            if (this.showTaxonomies) {
                if (item.rootId == null || this.dataItemsMap.get(item.rootId)?.isVisibleInGraph) {
                    return item.isVisibleInGraph;
                }
            }
            return false;
        }
        return false;
    }

    private childIsInBounds(item: DataItemModel): boolean {
        if (GROUP_DATA_ITEM_TYPE_SET.has(item.itemType)) {
            return true; // group nodes are always in bounds
        }
        if (TYPE_DATA_ITEM_TYPE_SET.has(item.itemType)) {
            return item.node.index < this.typeChildsToShow;
        }
        if (TAXONOMY_DATA_ITEM_TYPE_SET.has(item.itemType)) {
            return item.node.depth < (this.taxonomyLevelsToShow + 1);
        }
    }

    private itemOrChildIsSelected(item: DataItemModel): boolean {
        if (item.isSelected) {
            return true;
        }
        if (!GROUP_DATA_ITEM_TYPE_SET.has(item.itemType)) {
            return false; // only check children for top level groups
        }

        let childSelected = false;

        const checkChildren = (item: DataItemModel) => {
            if (childSelected) {
                return;
            }
            if (item.isSelected) {
                childSelected = true;
                return;
            }
            if (item.hasChildren()) {
                item.children.forEach(checkChildren);
            }
        };
        if (item.hasChildren()) {
            item.children.forEach(checkChildren);
        }
        return childSelected;
    }

    private itemOrParentHasEdge(item: DataItemModel): boolean {
        return this.dataItemsWithEdges.has(item.id) || (item.rootId && this.dataItemsWithEdges.has(item.rootId));
    }

    private shouldRenderItem(item: DataItemModel | null): boolean {
        if (item == null) {
            return false; // cannot render unknown items
        }
        // TODO
        // the item is visible based on its itemType
        const itemTypeVisible = this.itemTypeIsVisible(item);
        // check if child should be shown
        const itemInBounds = this.childIsInBounds(item);
        // the item should be hidden based on selection status (only if showSelectedItems === true)
        const isHiddenUnselected = this.showSelectedItems && !this.itemOrChildIsSelected(item);
        // item should be hidden becouse it has edges and only unconnected items should be displayed (only if showElementsWithoutAnEdge === true)
        const isHiddenConnected = this.showElementsWithoutAnEdge && this.itemOrParentHasEdge(item);
        return itemTypeVisible && itemInBounds && !isHiddenUnselected && !isHiddenConnected;
    }


    private renderGraph(isFirstRender = false) {
        if (this.graph == null) {
            return;
        }
        const gm = this.graph.groupingManager;
        // eslint-disable-next-line complexity
        this.dataItemsMap.forEach(item => {
            const shouldRender = this.shouldRenderItem(item);
            if (shouldRender) {
                // TODO render
                if (this.graph.getNode(item.node.id) == null) {
                    this.graph.addNode(item.node, false);

                    // handle items in groups (currently no nesting => everyone joins root group directly)
                    if (item.rootId != null) {
                        gm.addNodeToGroup(item.rootId, item.id, { x: item.node.x, y: item.node.y });
                    }

                    // handle minimap
                    if (GROUP_DATA_ITEM_TYPE_SET.has(item.itemType)) {
                        this.graphoverview.addNode(item.node);
                    }
                }

                // handle taxonomy edges
                if (item.itemType === DataItemTypeEnum.TaxonomyItemProperty && item.parentIds.size > 0) {
                    // set taxonomy edges
                    item.parentIds.forEach(nodeParent => {
                        if (this.dataItemsMap.get(nodeParent)?.itemType !== DataItemTypeEnum.TaxonomyItemProperty) {
                            return; // ignore edges coming from non taxonomy item nodes
                        }
                        const edge = {
                            source: nodeParent,
                            target: item.id,
                            dragHandles: [], // do not add drag handles
                            markerEnd: {
                                template: "arrow",
                                scaleRelative: true,
                                scale: 0.4,
                                relativeRotation: 0,
                            },
                        };
                        if (this.graph.getEdge(edgeId(edge)) == null) {
                            this.graph.addEdge(edge, false);
                        }
                    });
                }
            } else {
                if (this.graph.getNode(item.id) != null) {
                    // only delete if node is actually there
                    if (item.rootId != null) {
                        gm.removeNodeFromGroup(item.rootId, item.id);
                    }
                    this.graph.removeNode(item.id);
                }
            }

            // handle reference edges
            if (item.itemType === DataItemTypeEnum.TypeProperty || item.itemType === DataItemTypeEnum.TaxonomyProperty) {
                const parentItem = this.dataItemsMap.get(item.rootId);
                const targetItem = this.dataItemsMap.get(item.referenceTargetId);

                if (!(this.shouldRenderItem(parentItem) && this.shouldRenderItem(targetItem))) {
                    return; // both parents are not rendered => cannot draw edge
                }

                const referenceEdgeId = edgeId({ source: item.id, target: targetItem.id });

                const existingEdge = this.graph.getEdge(referenceEdgeId);

                const sourceId = shouldRender ? item.id : parentItem.id;

                if (existingEdge != null) {
                    // remove an existing edge attached to the parent
                    existingEdge.source = sourceId;
                } else {
                    const edge = {
                        id: referenceEdgeId,
                        source: sourceId,
                        target: targetItem.id,
                        sourceRoot: parentItem.id,
                        dragHandles: [], // do not add drag handles
                        markerEnd: {
                            template: "arrow",
                            scaleRelative: true,
                            scale: 0.4,
                            relativeRotation: 0,
                        },
                    };

                    this.graph.addEdge(edge, false);
                }

                // add edge to overview
                const overviewEdge = {
                    source: parentItem.id,
                    target: targetItem.id,
                    dragHandles: [], // do not add drag handles
                    markerEnd: {
                        template: "arrow",
                        scaleRelative: true,
                        scale: 0.4,
                        relativeRotation: 0,
                    },
                };
                if (this.graphoverview?.getEdge(edgeId(overviewEdge)) == null) {
                    // only add edge if edge is not already drawn!
                    this.graphoverview?.addEdge(overviewEdge, false);
                }
            }
        });
        this.graph.nodeList.sort((a, b) => (a?.z ?? Infinity) - (b?.z ?? Infinity));
        if (isFirstRender) {
            this.calculateNodePositions();
        }
        this.graph.completeRender();
        if (isFirstRender) {
            this.graph.zoomToBoundingBox();
        }
        this.graphoverview.completeRender();
        this.graphoverview.zoomToBoundingBox();
        this.isRendered = true;
    }

    /**
     * remove the searchresult higlighting
     */
    removeSearchResultsHighlighting() {
        this.graph.getSVG().selectAll("g.node")
            .nodes()
            .forEach(node => node.classList?.remove("greyedout-node"));
        this.dataItems.forEach(par => {
            par.isSearchResult = false;
            par.childIsInResult = false;
            par.visible = true;
            if (!par.isSelected) {
                this.graph.deselectNode(par.id);
            }
            let collapse: boolean = true;
            par.children.forEach(child => {
                child.isSearchResult = false;
                if (!child.isSelected) {
                    this.graph.deselectNode(child.id);
                }
                if (child.isSelected) {
                    collapse = false;
                }
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
        const allEdgeConnections = [];
        this.graph.edgeList.forEach(edge => allEdgeConnections.push(edge.target, edge.source));

        // set the checkboxes to false
        this.showTypes = false;
        this.showTaxonomies = false;

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
            });
        });
        this.updateVisibilityInGraph();
    }

    private updateGraphoverviewNodePositions() {
        this.graphoverview?.updateGraphPositions();
        this.graphoverview?.zoomToBoundingBox();

    }

    private updateLayout() {
        if (this.graph == null) {
            return;
        }
        this.calculateNodePositions();
        this.graph?.updateGraphPositions();
        this.updateGraphoverviewNodePositions();
    }

    /**
     * calcualte the position of the nodes based on the selected layout algorithm
     */
    private calculateNodePositions() {
        if (this.graph == null) {
            return;
        }

        let distance: number | string = this.distanceBetweenElements;
        if (typeof distance === "string") {
            distance = parseInt(distance, 10);
        }

        if (this.selectedLayoutAlgorithmId == 0) {
            calculateNodePositionsNgraph(this.graph, distance);
        } else if (this.selectedLayoutAlgorithmId == 1) {
            calculateNodePositionsd3(this.graph, distance);
        }
    }

    /**
     * sort all dataitems in an alphabetical order
     * @param items dataitems list
     */
    private sortList(items: DataItemModel[]) {
        items.sort(function (a, b) {
            const nameA = a.name.toUpperCase(); // ignore upper and lowercase
            const nameB = b.name.toUpperCase(); // ignore upper and lowercase
            if (nameA < nameB) {
                return -1;
            }
            if (nameA > nameB) {
                return 1;
            }

            // names must be equal
            return 0;
        });
        items.forEach(item => this.sortList(item.children));
    }


    /**
     * update the visibility of all nodes in the graph based on the dataitems isVisibleInGraph value
     */
    private updateVisibilityInGraph() {
        this.graph.getSVG().selectAll("g.edge-group")
            .nodes()
            .forEach(edge => {
                edge.classList?.remove("invisible-node");
            });

        this.dataItems.forEach(node => {
            if (node.isVisibleInGraph) {
                this.graph.getSVG().select(`#node-${node.id}`)
                    .node()?.classList?.remove("invisible-node");
                this.graphoverview.getSVG().select(`#node-${node.id}`)
                    .node()?.classList?.remove("invisible-node");
            } else {
                this.graph.getSVG().select(`#node-${node.id}`)
                    .node()?.classList?.add("invisible-node");
                this.graphoverview.getSVG().select(`#node-${node.id}`)
                    .node()?.classList?.add("invisible-node");
                this.updateVisibilityOfEdge(node.id, false);
            }
            node.children.forEach(child => {
                if (child.isVisibleInGraph) {
                    this.graph.getSVG().select(`#node-${child.id}`)
                        .node()?.classList?.remove("invisible-node");
                    this.graphoverview.getSVG().select(`#node-${child.id}`)
                        .node()?.classList?.remove("invisible-node");
                } else {
                    this.graph.getSVG().select(`#node-${child.id}`)
                        .node()?.classList?.add("invisible-node");
                    this.graphoverview.getSVG().select(`#node-${child.id}`)
                        .node()?.classList?.add("invisible-node");
                    this.updateVisibilityOfEdge(child.id, false);
                }
            });
        });
    }

    /**
     * update the visibility of an edge in the graph
     * @param nodeid all edges of this id should be hidden or shown, based on the visibile param
     * @param visibile show or hide the edges
     */
    private updateVisibilityOfEdge(nodeid: string, visibile: boolean) {
        this.graph.getSVG().selectAll("g.edge-group")
            .nodes()
            .forEach(edge => {
                if (edge.id.includes(nodeid)) {
                    if (visibile) {
                        edge.classList?.remove("invisible-node");
                    } else {
                        edge.classList?.add("invisible-node");
                    }
                }
            });
        this.graphoverview.getSVG().selectAll("g.edge-group")
            .nodes()
            .forEach(edge => {
                if (edge.id.includes(nodeid)) {
                    if (visibile) {
                        edge.classList?.remove("invisible-node");
                    } else {
                        edge.classList?.add("invisible-node");
                    }
                }
            });
    }

    /**
     * reposition all nodes back to the calculated positions
     */
    repositionNodes() {
        //this.dataItems.filter(p => !p.abstract).forEach(parent => {
        //    this.graph.moveNode(parent.id, parent.position.x, parent.position.y);
        //    this.graphoverview.moveNode(parent.id, parent.position.x, parent.position.y);
        //});
        //this.graph.completeRender();
        this.calculateNodePositions();
        this.resetLayout();
        this.graphoverview.completeRender();
        this.graphoverview.zoomToBoundingBox(true);
    }









    private onNodeClick(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node, key: string }>) {
        event.preventDefault(); // always prevent default as selection is handled by the data items!
        if (event.detail.eventSource !== "USER_INTERACTION") {
            return;
        }
        const node = event.detail.node;
        const item = this.dataItemsMap.get(node.id.toString());

        if (event.detail.key === "header") {
            this.selectedNode = item;
            item.isSelected = true;
            return;
        }
        item.isSelected = !item.isSelected;
    }

    private onSelectionChanged(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", selection: Set<string | number> }>) {
        const selection = event.detail.selection;
        if (this.selectedNode != null && !selection.has(this.selectedNode.id)) {
            this.selectedNode = null; // node is no longer selected in graph
        }

        if (this.showSelectedItems) {
            const gm = this.graph.groupingManager;
            const selectionCopy = new Set(selection);
            let extraNodesFound = false;
            this.graph.nodeList.forEach(node => {
                if (extraNodesFound) {
                    return;
                }
                if (!selection.has(node.id)) {
                    // node is not selected, check children
                    const childSelected = Array.from(gm.getAllChildrenOf(node.id)).some(childId => selection.has(childId));
                    if (!childSelected) {
                        extraNodesFound = true;
                        return;
                    }
                }
                selectionCopy.delete(node.id);
            });
            if (extraNodesFound || selection.size > 0) {
                // graph contains unselected nodes || not all selected nodes are rendered
                this.renderGraph();
            }
        }
    }


    private onBackgroundClick(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node }>) {
        this.graph.changeSelected(new Set()); // deselect everything
    }

    currentEdgeStyleBoldChanged(newValue: boolean) {
        if (this.graph == null) {
            return;
        }
        // needs a complete update of all edges
        this.graph.updateEdgeGroupClasses();
        this.graph.updateGraphPositions();
    }


    private onZoomChange(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node }>) {
        this.renderMainViewPositionInOverviewGraph();
        if (this.graph == null) {
            return;
        }
        if (this.graph.currentViewWindow.width <= document.getElementById("maingraphpart").offsetWidth * 2) {
            this.currentEdgeStyleBold = false;
        } else {
            this.currentEdgeStyleBold = true;
        }
    }

    private onNodePositionChange(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node }>) {
        if (event.detail.eventSource === "USER_INTERACTION") {
            // update minimap after user interactions
            if (this.graphoverview?.getNode(event.detail.node.id) != null) {
                // but only if minimap has that node
                this.updateGraphoverviewNodePositions();
            }
        }
        // always update fixed node coordinates when a node is moved!
        const node = event.detail.node;
        if (node.fx != null) {
            node.fx = node.x;
        }
        if (node.fy != null) {
            node.fy = node.y;
        }
    }

    private onNodeDragEnd(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node }>) {
        if (event.detail.eventSource === "USER_INTERACTION") {
            // update minimap after a node was dragged that requires a full render
            const item = this.dataItemsMap.get(event.detail.node.id.toString());
            if (CHILD_ITEM_TYPE_SET.has(item?.itemType)) {
                this.graphoverview?.completeRender();
                this.graphoverview?.zoomToBoundingBox();
            }
        }
    }

    private renderMainViewPositionInOverviewGraph() {
        const currentView = this.graph?.currentViewWindow;
        const svg = this.graphoverview?.getSVG();
        if (currentView == null || svg == null) {
            return;
        }
        svg.select("rect.view-window")
            .attr("x", currentView.x)
            .attr("y", currentView.y)
            .attr("width", currentView.width)
            .attr("height", currentView.height);

    }

    // function called by buttons from the front-end, to interact with the graph
    private zoomIn() {
        const zoomBox = this.graph.currentViewWindow;
        const newBox: Rect = { x: 0, y: 0, width: 0, height: 0 };
        newBox.width = zoomBox.width - zoomBox.width * 0.2;
        newBox.height = zoomBox.height - zoomBox.height * 0.2;
        newBox.x = zoomBox.x + (zoomBox.width - newBox.width) * 0.5;
        newBox.y = zoomBox.y + (zoomBox.height - newBox.height) * 0.5;
        this.graph.zoomToBox(newBox);
    }

    // function called by buttons from the front-end, to interact with the graph
    private zoomOut() {
        const zoomBox = this.graph.currentViewWindow;
        const newBox: Rect = { x: 0, y: 0, width: 0, height: 0 };
        newBox.width = zoomBox.width + zoomBox.width * 0.2;
        newBox.height = zoomBox.height + zoomBox.height * 0.2;
        newBox.x = zoomBox.x + (zoomBox.width - newBox.width) * 0.5;
        newBox.y = zoomBox.y + (zoomBox.height - newBox.height) * 0.5;
        this.graph.zoomToBox(newBox);
    }

    // function called by buttons from the front-end, to interact with the graph
    private toggleMaximize() {
        this.maximized = !this.maximized;
        if (this.maximized) {
            document.getElementById("mainontology-graph").style.height = "100%";
            document.getElementById("ontology-graph").style.padding = "0px";
        } else {
            document.getElementById("mainontology-graph").style.height = "500px";
            document.getElementById("ontology-graph").style.padding = "";
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
    private moveGraph(direction: string) {
        const dirX = this.graph.currentViewWindow.width / 20;
        const dirY = this.graph.currentViewWindow.height / 20;

        const element = document.getElementById("graphexportsvg").shadowRoot.querySelector(".graph-editor").querySelector("g.zoom-group");
        const transformsettings = element.getAttribute("transform");
        let width: number = Number(transformsettings.split("(")[1].split(",")[0]);
        let height: number = Number(transformsettings.split("(")[1].split(",")[1].split(")")[0]);
        const scaling = transformsettings.split("(")[2].split(")")[0];

        if (direction === "down") {
            height += dirY;
        } else if (direction === "right") {
            width += dirX;
        } else if (direction === "left") {
            width -= dirX;
        } else if (direction === "up") {
            height -= dirY;
        }

        element.setAttribute("transform", `translate(${width},${height}) scale(${scaling})`);
    }

    private showSelectedItemsFunction() {
        this.showTypes = false;
        this.showTaxonomies = false;
        this.dataItems.forEach(parent => {
            if (parent.isSelected) {
                parent.isVisibleInGraph = true;
            } else {
                parent.isVisibleInGraph = false;
                parent.children.forEach(child => {
                    if (child.isSelected) {
                        child.isVisibleInGraph = true;
                        parent.isVisibleInGraph = true;
                    }
                });
            }
        });
        this.updateVisibilityInGraph();
    }

    unselectNode() {
        this.selectedNode = null;
    }

    private downloadSVG() {
        // TODO: dowload svg
        /*const PDFDocument = require("pdfkit"),
            SVGtoPDF = require("svg-to-pdfkit");

        const doc = new PDFDocument(),
            stream = fs.createWriteStream("file.pdf");

        SVGtoPDF(doc, this.graph.getSVG, 0, 0);

        stream.on("finish", function () {
            console.log(fs.readFileSync("file.pdf"));
        });

        doc.pipe(stream);
        doc.end();*/
    }

    storedViewWindow: Rect;

    private tempZoomOut(state) {
        if (state == "on") {
            this.storedViewWindow = this.graph.currentViewWindow;
            this.graph.zoomToBoundingBox();
        } else {
            this.graph.zoomToBox(this.storedViewWindow);
        }
    }

    isMainDragging: boolean = false;
    isLeftUpperDragging: boolean = false;
    isLeftLowerDragging: boolean = false;
    startDraggingPosition;

    endDrag() {
        if (this.isMainDragging || this.isLeftUpperDragging || this.isLeftLowerDragging) {
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

    startLeftLowerDrag(event) {
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
        document.getElementById("mainontology-graph").addEventListener("mouseup", e => this.endDrag());
        //mousemove.delegate="onDrag($event)"
        document.getElementById("mainontology-graph").addEventListener("mousemove", e => this.onDrag(e));
        //mouseleave.delegate="endDrag()"
        document.getElementById("mainontology-graph").addEventListener("mouseleave", e => this.endDrag());
    }

    onDrag(event) {
        if (this.isMainDragging) {
            const page = document.getElementById("mainontology-graph");
            const searchArea = document.getElementById("menu-section");
            const graphArea = document.getElementById("maingraphpart");

            const leftColWidth = searchArea.clientWidth + 4;
            const rightColWidth = graphArea.clientWidth + 4;

            const dragbarWidth = 2;
            const move = event.clientX - this.startDraggingPosition;
            const total = leftColWidth + dragbarWidth + rightColWidth;
            const cols = [
                ((leftColWidth + move) / total) * 100,
                (dragbarWidth / total) * 100,
                ((rightColWidth - move) / total) * 100,
            ];
            const newColDefn = cols.map(c => `${c.toString()}%`).join(" ");
            page.style.gridTemplateColumns = newColDefn;

            this.startDraggingPosition = event.clientX;
            event.preventDefault();
        } else if (this.isLeftUpperDragging) {
            const menusection = document.getElementById("menu-section");
            const filterSubarea = document.getElementById("item-filtersection");
            const treeSubarea = document.getElementById("item-treesection");
            const overviewSubarea = document.getElementById("item-overview");


            const filterHeight = filterSubarea.clientHeight + 1;
            const treeHeight = treeSubarea.clientHeight + 1;
            const overviewHeight = overviewSubarea.clientHeight;

            const total = filterHeight + treeHeight + overviewHeight;
            const move = event.clientY - this.startDraggingPosition;
            const cols = [
                ((filterHeight + move) / total) * 100,
                ((treeHeight - move) / total) * 100,
                ((overviewHeight) / total) * 100,
            ];
            const newColDefn = cols.map(c => `${c.toString()}%`).join(" ");
            menusection.style.gridTemplateRows = newColDefn;

            this.startDraggingPosition = event.clientY;
            event.preventDefault();

        } else if (this.isLeftLowerDragging) {
            const menusection = document.getElementById("menu-section");
            const filterSubarea = document.getElementById("item-filtersection");
            const treeSubarea = document.getElementById("item-treesection");
            const overviewSubarea = document.getElementById("item-overview");


            const filterHeight = filterSubarea.clientHeight + 1;
            const treeHeight = treeSubarea.clientHeight + 1;
            const overviewHeight = overviewSubarea.clientHeight;

            const total = filterHeight + treeHeight + overviewHeight;
            const move = event.clientY - this.startDraggingPosition;
            const cols = [
                ((filterHeight) / total) * 100,
                ((treeHeight + move) / total) * 100,
                ((overviewHeight - move) / total) * 100,
            ];
            const newColDefn = cols.map(c => `${c.toString()}%`).join(" ");
            menusection.style.gridTemplateRows = newColDefn;

            this.startDraggingPosition = event.clientY;
            event.preventDefault();
        }
    }
}
