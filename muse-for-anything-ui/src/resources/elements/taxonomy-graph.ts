import { bindable, autoinject, observable, child } from "aurelia-framework";
import { EventAggregator, Subscription } from "aurelia-event-aggregator";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiLinkKey, ApiObject, ApiResponse, ChangedApiObject, isChangedApiObject, isNewApiObject, NewApiObject } from "rest/api-objects";
import { NavigationLinksService } from "services/navigation-links";
import { API_RESOURCE_CHANGES_CHANNEL } from "resources/events";
import GraphEditor from "@ustutt/grapheditor-webcomponent/lib/grapheditor";
import { Node } from "@ustutt/grapheditor-webcomponent/lib/node";
import { DraggedEdge, Edge, edgeId } from "@ustutt/grapheditor-webcomponent/lib/edge";
import { PropertyDescription } from "rest/schema-objects";
import { SchemaService } from "rest/schema-service";


export interface TaxonomyApiObject extends ApiObject {
    name: string;
    description: string | null;
    items: ApiLink[];
    collectionSize: number;
}

export interface TaxonomyItemApiObject extends ApiObject {
    name: string;
    description: string | null;
    sortKey: number | null;
    parents: ApiLink[];
    children: ApiLink[];
    isToplevelItem: boolean;
    deletedOn: string | null;
    // TODO missing
}

export interface TaxonomyItemRelationApiObject extends ApiObject {
    sourceItem: ApiLink;
    targetItem: ApiLink;
    deletedOn: string | null;
}

function apiLinkToId(link: ApiLink): string {
    if (link == null || link.resourceKey == null) {
        throw Error("Cannot create id from empty api link or a link without a resourceKey!");
    }
    const entries = Object.keys(link.resourceKey)
        .sort()
        .map(key => link.resourceKey[key]);
    return `${link.resourceType}-${entries.join("-")}`;
}

class TaxonomyItemNode implements Node {
    readonly id: string;
    readonly type = "taxonomy-item";

    private internalData: ApiResponse<TaxonomyItemApiObject>;

    x = 0;
    y = 0;

    level: number = 0;

    updateItemAction: ApiLink;
    deleteItemAction: ApiLink;
    restoreItemAction: ApiLink;
    createRelationAction: ApiLink;

    constructor(data: ApiResponse<TaxonomyItemApiObject>) {
        this.id = apiLinkToId(data.data.self);
        this.data = data;
    }

    set data(data: ApiResponse<TaxonomyItemApiObject>) {
        this.updateItemAction = data.links.find(link => link.resourceType === "ont-taxonomy-item" && link.rel.some(rel => rel === "update"));
        this.deleteItemAction = data.links.find(link => link.resourceType === "ont-taxonomy-item" && link.rel.some(rel => rel === "delete"));
        this.restoreItemAction = data.links.find(link => link.resourceType === "ont-taxonomy-item" && link.rel.some(rel => rel === "restore"));
        this.createRelationAction = data.links.find(link => link.resourceType === "ont-taxonomy-item-relation" && link.rel.some(rel => rel === "create"));
        this.internalData = data;
    }

    get data(): ApiResponse<TaxonomyItemApiObject> {
        return this.internalData;
    }

    get title() {
        return this.data?.data?.name ?? this.id;
    }

    get description() {
        return this.data?.data?.description ?? "";
    }

    get sortKey() {
        const key = this.data?.data?.sortKey;
        if (key != null) {
            return key.toString();
        }
        return "";
    }

    get isTopLevel(): boolean {
        return this.data?.data?.isToplevelItem ?? false;
    }

    get deleted() {
        return this.data?.data?.deletedOn != null;
    }
}

// eslint-disable-next-line complexity
function taxonomyItemNodeComparator(a: TaxonomyItemNode, b: TaxonomyItemNode) {
    if (a.deleted && !b.deleted) { // deleted items are sorted to the end
        return 1;
    }
    if (!a.deleted && b.deleted) {
        return -1;
    }
    const sortKey = (a?.data?.data?.sortKey ?? 0) - (b?.data?.data?.sortKey ?? 0);
    if (sortKey < 0) { // sort key trumps everything
        return -1;
    }
    if (sortKey > 0) {
        return 1;
    }
    if (a.title < b.title) { // sort by name when same sortKey
        return -1;
    }
    if (a.title > b.title) {
        return 1;
    }
    if (a.id < b.id) { // sort by id when same name and sortKey
        return -1;
    }
    if (a.id > b.id) {
        return 1;
    }
    return 0;
}

class ItemRelationEdge implements Edge {
    readonly id: string;
    readonly type: string = "item-relation";

    private internalData: ApiResponse<TaxonomyItemRelationApiObject>;

    private internalSource: string;
    private internalTarget: string;

    deleteAction: ApiLink;

    dragHandles = [
        {
            "template": "default-marker",
            "positionOnLine": 0.95,
            "absolutePositionOnLine": -25,
        },
    ];

    markerEnd = {
        template: "arrow",
        scale: 0.8,
        relativeRotation: 0,
    };

    constructor(data: ApiResponse<TaxonomyItemRelationApiObject>) {
        this.id = apiLinkToId(data.data.self);
        this.data = data;
    }

    set data(data: ApiResponse<TaxonomyItemRelationApiObject>) {
        this.internalSource = apiLinkToId(data.data.sourceItem);
        this.internalTarget = apiLinkToId(data.data.targetItem);
        this.deleteAction = data.links.find(link => link.resourceType === "ont-taxonomy-item-relation" && link.rel.some(rel => rel === "delete"));
        this.internalData = data;
    }

    get data(): ApiResponse<TaxonomyItemRelationApiObject> {
        return this.internalData;
    }

    get source() {
        return this.internalSource;
    }

    get target() {
        return this.internalTarget;
    }

    get deleted() {
        return this.data?.data?.deletedOn != null;
    }
}


@autoinject
export class TaxonomyGraph {
    @bindable apiLink;
    @bindable ignoreCache = false;

    @observable() apiObject: TaxonomyApiObject;
    @observable() createItemAction: ApiLink;

    maximized: boolean = false;

    showForm: boolean = false;
    formProperties: PropertyDescription[];
    formData: { name: string, description: string, sortKey: number } = { name: "", description: "", sortKey: 0 };
    initialFormData: { name: string, description: string, sortKey: number } = { name: "", description: "", sortKey: 0 };
    propertiesValid: { name: boolean, description: boolean, sortKey: boolean } = { name: false, description: false, sortKey: false };
    propertiesDirty: { name: boolean, description: boolean, sortKey: boolean } = { name: false, description: false, sortKey: false };
    savingForm: boolean = false;

    @child("network-graph.graph") graph: GraphEditor;

    @observable() selectedNode: TaxonomyItemNode;

    private api: BaseApiService;
    private schemaService: SchemaService;
    private navService: NavigationLinksService;
    private events: EventAggregator;

    private subscription: Subscription;

    constructor(baseApi: BaseApiService, schemas: SchemaService, navService: NavigationLinksService, events: EventAggregator) {
        this.api = baseApi;
        this.schemaService = schemas;
        this.navService = navService;
        this.events = events;
        this.subscribe();
    }

    subscribe(): void {
        this.subscription = this.events.subscribe(API_RESOURCE_CHANGES_CHANNEL, (resourceKey: ApiLinkKey) => {
            const selfKey: ApiLinkKey = this.apiObject?.self.resourceKey;
            if (selfKey == null || Object.keys(selfKey).length === 0) {
                return;
            }
            if (Object.keys(selfKey).every(key => selfKey[key] === resourceKey[key])) {
                // current object is a sub key
                this.loadData(this.apiLink, false);
            }
        });
    }

    apiLinkChanged(newValue: ApiLink, oldValue) {
        this.apiObject = null;
        this.formProperties = null;
        this.loadData(this.apiLink, this.ignoreCache);
    }

    private loadData(apiLink: ApiLink, ignoreCache: boolean) {
        this.api.getByApiLink<TaxonomyApiObject>(apiLink, ignoreCache).then(apiResponse => {
            if (apiResponse.data.self.resourceType !== "ont-taxonomy") {
                console.error("Can only display graph for taxonomy objects!", apiResponse.data);
                return;
            }
            this.apiObject = apiResponse.data; // FIXME use proper type checking for api response…
            this.createItemAction = apiResponse.links.find(link => link.resourceType === "ont-taxonomy-item" && link.rel.some(rel => rel === "create"));
        });
    }

    apiObjectChanged(newValue: TaxonomyApiObject, oldValue) {
        if (newValue == null) {
            this.resetGraph();
            return;
        }
        const itemPromises = [];
        const relationPromises = [];
        const items: Array<ApiResponse<TaxonomyItemApiObject>> = [];
        const relations: Array<ApiResponse<TaxonomyItemRelationApiObject>> = [];
        newValue.items.forEach(itemLink => {
            itemPromises.push(this.api.getByApiLink<TaxonomyItemApiObject>(itemLink, false).then(apiResponse => {
                items.push(apiResponse);
                apiResponse.data.children.forEach(childRelationLink => {
                    relationPromises.push(this.api.getByApiLink<TaxonomyItemRelationApiObject>(childRelationLink, false).then(relationApiResponse => {
                        relations.push(relationApiResponse);
                    }));
                });
            }));
        });
        Promise.all(itemPromises)
            .then(() => Promise.all(relationPromises))
            .then(() => this.setTaxonomyData(items, relations));
    }

    createItemActionChanged(newAction: ApiLink, oldAction) {
        if (newAction == null || newAction.schema == null) {
            return;
        }
        this.schemaService.getSchema(newAction.schema)
            .then(schema => schema.getNormalizedApiSchema())
            .then(normalized => {
                this.formProperties = normalized.getPropertyList([], { allowList: ["name", "description", "sortKey"] });
            });
    }

    selectedNodeChanged(newSelected, oldSelected) {
        this.showForm = false;
        if (newSelected == null) {
            // reset form data
            this.formData = {
                name: "",
                description: "",
                sortKey: 0,
            };
            this.initialFormData = {
                name: "",
                description: "",
                sortKey: 0,
            };
        } else {
            this.initialFormData = {
                name: newSelected.title,
                description: newSelected.description,
                sortKey: newSelected.data.data.sortKey,
            };
        }
    }

    toggleMaximize() {
        this.maximized = !this.maximized;
    }

    addItem() {
        if (this.createItemAction == null || this.formProperties == null || this.selectedNode != null) {
            return;
        }
        this.showForm = !this.showForm;
    }

    editSelectedItem() {
        if (this.selectedNode == null || this.formProperties == null) {
            return;
        }

        this.formData = {
            name: this.selectedNode.title,
            description: this.selectedNode.description,
            sortKey: this.selectedNode.data.data.sortKey,
        };
        this.showForm = !this.showForm;
    }

    deleteSelectedItem() {
        if (this.selectedNode == null || this.formProperties == null) {
            return;
        }
        if (this.selectedNode.deleteItemAction == null) {
            return;
        }

        this.restoreOrDeleteSelectedItem(this.selectedNode.deleteItemAction);
    }

    restoreSelectedItem() {
        if (this.selectedNode == null || this.formProperties == null) {
            return;
        }
        if (this.selectedNode.restoreItemAction == null) {
            return;
        }

        this.restoreOrDeleteSelectedItem(this.selectedNode.restoreItemAction);
    }

    private restoreOrDeleteSelectedItem(action: ApiLink) {
        this.api.submitByApiLink<ChangedApiObject>(action).then(result => {
            const promises = [];
            result.links.forEach(link => {
                if (link.resourceType === "ont-taxonomy-item") {
                    // reload changed taxonomy items
                    const promise = this.api.getByApiLink<TaxonomyItemApiObject>(link).then(itemResult => {
                        const nodeId = apiLinkToId(itemResult.data.self);
                        const itemNode = this.graph.getNode(nodeId);
                        if (itemNode != null) {
                            itemNode.data = itemResult;
                        } else {
                            // new node
                            this.graph.addNode(new TaxonomyItemNode(itemResult));
                        }
                    });
                    promises.push(promise);
                } else if (link.resourceType === "ont-taxonomy-item-relation") {
                    // reload changed taxonomy items relations
                    const promise = this.api.getByApiLink<TaxonomyItemRelationApiObject>(link).then(relationResult => {
                        const edge = new ItemRelationEdge(relationResult);
                        if (edge.deleted) {
                            this.graph.removeEdge(edge.id);
                        } else {
                            const existingEdge = this.graph.getEdge(edge.id);
                            if (existingEdge != null) {
                                existingEdge.data = relationResult;
                            } else {
                                this.graph.addEdge(edge);
                            }
                        }
                    });
                    promises.push(promise);
                }
            });
            return Promise.all(promises).then(() => {
                this.graph.completeRender();
                this.layout();
            });
        });
    }

    submitForm() {
        if (!this.propertiesValid.name || !this.propertiesValid.description || !this.propertiesValid.sortKey) {
            return; // invalid form data
        }
        if (this.savingForm) {
            return; // save request already running
        }
        let submitLink: ApiLink;
        if (this.selectedNode == null) {
            submitLink = this.createItemAction;
        }
        if (this.selectedNode != null) {
            submitLink = this.selectedNode.updateItemAction;
        }
        if (submitLink == null) {
            return; // no submit action
        }

        this.savingForm = true;
        this.api.submitByApiLink<NewApiObject | ChangedApiObject>(submitLink, this.formData)
            .then(result => {
                this.showForm = false;
                const promises = [];
                result.links.forEach(link => {
                    if (link.resourceType !== "ont-taxonomy-item") {
                        return;
                    }
                    // reload changed taxonomy items
                    const promise = this.api.getByApiLink<TaxonomyItemApiObject>(link).then(itemResult => {
                        const nodeId = apiLinkToId(itemResult.data.self);
                        const itemNode = this.graph.getNode(nodeId);
                        if (itemNode != null) {
                            itemNode.data = itemResult;
                        } else {
                            // new node
                            this.graph.addNode(new TaxonomyItemNode(itemResult));
                        }
                    });
                    promises.push(promise);
                });
                return Promise.all(promises).then(() => {
                    this.graph.completeRender();
                    this.layout();
                });
            })
            .finally(() => this.savingForm = false);

    }

    private resetGraph() {
        if (this.graph == null) {
            return; // no graph -> nothing to reset
        }
        this.selectedNode = null;
        this.graph.nodeList = [];
        // todo reset groups if groups are used!
        this.graph.completeRender();
    }

    private setTaxonomyData(items: Array<ApiResponse<TaxonomyItemApiObject>>, relations: Array<ApiResponse<TaxonomyItemRelationApiObject>>) {
        if (this.graph == null) {
            return;
        }
        items.forEach(itemData => {
            const node = new TaxonomyItemNode(itemData);
            const existingNode: TaxonomyItemNode = this.graph.getNode(node.id) as TaxonomyItemNode; // TODO proper type checking
            if (existingNode == null) {
                this.graph.addNode(node);
            } else {
                existingNode.data = itemData;
            }
        });
        const existingEdges = new Set<string>();
        this.graph.edgeList.forEach(edge => {
            if (edge.type === "item-relation") {
                existingEdges.add(edgeId(edge));
            }
        });
        relations.forEach(relationData => {
            const edge = new ItemRelationEdge(relationData);
            if (edge.deleted) {
                return; // do not add already deleted edges to the graph
            }
            if (this.graph.getEdge(edge.id) == null) {
                // relations cannot be edited in the api so only adding / removing is needed
                this.graph.addEdge(edge);
            }
            existingEdges.delete(edge.id); // remove edge from set if found/created
        });
        // remove all preexisting edges that were not found/created
        existingEdges.forEach(edgeId => this.graph.removeEdge(edgeId));
        this.graph.completeRender();
        this.resetLayout();
    }

    resetLayout() {
        this.layout();
        this.graph?.zoomToBoundingBox();
    }

    private layout() {
        if (this.graph == null) {
            return;
        }
        const startNodes: TaxonomyItemNode[] = this.graph.nodeList.filter(node => node.type === "taxonomy-item" && node.isTopLevel) as TaxonomyItemNode[]; // TODO proper type checking
        const recursiveLevelAssign = (node: TaxonomyItemNode, level: number) => {
            node.level = level;
            const related = this.graph.getEdgesBySource(node.id);
            related.forEach(edge => {
                if (edge.type !== "item-relation") {
                    return;
                }
                const targetNode = this.graph.getNode(edge.target);
                if (targetNode?.type === "taxonomy-item") {
                    recursiveLevelAssign(targetNode as TaxonomyItemNode, level + 1);
                }
            });
        };
        startNodes.forEach(node => recursiveLevelAssign(node, 0));

        startNodes.sort(taxonomyItemNodeComparator);

        const layoutedNodes = new Set<string>();

        let currentY = 0;

        const recursivePositionAssign = (node: TaxonomyItemNode, isFirstChildItem = false) => {
            if (layoutedNodes.has(node.id)) {
                return;
            }
            layoutedNodes.add(node.id);
            if (isFirstChildItem) {
                currentY -= 80;
            }
            node.x = node.level * 220;
            node.y = currentY;
            currentY += 80;
            const related = this.graph.getEdgesBySource(node.id);
            const relatedNodes: Node[] = [];
            related.forEach(edge => {
                if (edge.type !== "item-relation") {
                    return;
                }
                if (!layoutedNodes.has(edge.target as string)) {
                    relatedNodes.push(this.graph.getNode(edge.target));
                }
            });
            relatedNodes.sort(taxonomyItemNodeComparator);
            relatedNodes.forEach((node, index) => {
                if (node?.type === "taxonomy-item") {
                    recursivePositionAssign(node as TaxonomyItemNode, index === 0);
                }
            });
        };
        startNodes.forEach(node => recursivePositionAssign(node));
        this.graph.updateGraphPositions();
    }

    graphChanged(newGraph: GraphEditor, oldGraph) {
        if (newGraph == null) {
            return;
        }
        newGraph.addEventListener("backgroundclick", (event) => this.onBackgroundClick(event as any));
        newGraph.addEventListener("nodeclick", (event) => this.onNodeClick(event as any));
        newGraph.onCreateDraggedEdge = (edge: DraggedEdge) => this.onCreateDraggedEdge(edge);
        newGraph.addEventListener("edgeadd", (event) => this.onEdgeAdd(event as any));
        newGraph.addEventListener("edgeremove", (event) => this.onEdgeRemove(event as any));

        newGraph.setNodeClass = (className: string, node: Node): boolean => this.setNodeClass(className, node);
    }

    private setNodeClass(className: string, node: Node): boolean {
        if (className === node.type) {
            return true;
        }
        if (className === "deleted" && node.deleted) {
            return true;
        }
        return false;
    }

    private onBackgroundClick(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node }>) {
        if (this.selectedNode != null) {
            this.graph.deselectNode(this.selectedNode.id);
            this.selectedNode = null;
        }
    }

    private onNodeClick(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node }>) {
        if (event.detail.eventSource !== "USER_INTERACTION") {
            return;
        }
        event.preventDefault();
        const node = event.detail.node;
        if (node.type !== "taxonomy-item") {
            return;
        }
        if (this.selectedNode?.id === node.id) {
            this.graph.deselectNode(node.id);
            this.selectedNode = null;
            this.graph.updateHighlights();
        } else {
            if (this.selectedNode != null) {
                this.graph.deselectNode(this.selectedNode.id);
            }
            this.graph.selectNode(node.id);
            this.selectedNode = node as TaxonomyItemNode; // TODO correct type checking
            this.graph.updateHighlights();
        }
    }

    private getNodeParents(node, parentsSet?: Set<string>): Set<string> {
        if (parentsSet == null) {
            parentsSet = new Set();
        }
        if (node.type !== "taxonomy-item") {
            return;
        }

        parentsSet.add(node.id);
        const parentItems = this.graph.getEdgesByTarget(node.id);
        parentItems.forEach(edge => {
            const node = this.graph.getNode(edge.source);
            if (node != null) {
                this.getNodeParents(node, parentsSet);
            }
        });

        return parentsSet;
    }

    private onCreateDraggedEdge(edge: DraggedEdge): DraggedEdge {
        if (edge.createdFrom != null) {
            edge.validTargets.clear(); // only allow dropping the edge in the void!
            const originEdge = this.graph.getEdge(edge.createdFrom);
            edge.validTargets.add(originEdge.target.toString());
        } else {
            edge.type = "item-relation";
            edge.markerEnd = {
                template: "arrow",
                scale: 0.8,
                relativeRotation: 0,
            };
            edge.validTargets.clear();
            const sourceNode = this.graph.getNode(edge.source);
            const forbiddenNodes = this.getNodeParents(sourceNode);
            const existingEdges = this.graph.getEdgesBySource(sourceNode.id);
            existingEdges.forEach(edge => forbiddenNodes.add(edge.target.toString()));
            this.graph.nodeList.forEach(node => {
                if (node.type !== "taxonomy-item") {
                    return;
                }
                if (forbiddenNodes.has((node as TaxonomyItemNode).id)) {
                    return;
                }
                edge.validTargets.add((node as TaxonomyItemNode).id);
            });
        }
        return edge;
    }

    private onEdgeAdd(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", edge: Edge }>) {
        if (event.detail.eventSource !== "USER_INTERACTION") {
            return;
        }
        event.preventDefault();
        const edge = event.detail.edge as ItemRelationEdge;
        const sourceNode = this.graph.getNode(edge.source) as TaxonomyItemNode;
        if (sourceNode?.type === "taxonomy-item" && sourceNode.createRelationAction != null) {
            const targetNode = this.graph.getNode(edge.target) as TaxonomyItemNode;
            if (targetNode?.type !== "taxonomy-item") {
                return; // wrong node type
            }
            this.api.submitByApiLink<NewApiObject>(sourceNode.createRelationAction, targetNode.data.data.self.resourceKey).then(result => {
                if (!isNewApiObject(result.data)) {
                    console.error("Got wrong response type from API.");
                    return;
                }
                const promises = [
                    this.api.getByApiLink<TaxonomyItemRelationApiObject>(result.data.new).then(newEdgeResult => {
                        const newEdge = new ItemRelationEdge(newEdgeResult);
                        if (this.graph.getEdge(newEdge.id) == null) {
                            this.graph.addEdge(newEdge);
                        }
                    }),
                ];
                result.links.forEach(link => {
                    if (link.resourceType !== "ont-taxonomy-item") {
                        return;
                    }
                    // reload changed taxonomy items
                    const promise = this.api.getByApiLink<TaxonomyItemApiObject>(link).then(itemResult => {
                        const nodeId = apiLinkToId(itemResult.data.self);
                        const itemNode = this.graph.getNode(nodeId);
                        if (itemNode != null) {
                            itemNode.data = itemResult;
                        }
                    });
                    promises.push(promise);
                });
                Promise.all(promises).then(() => {
                    this.graph.completeRender();
                    this.layout();
                });
            });
        }
    }

    private onEdgeRemove(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", edge: Edge }>) {
        if (event.detail.eventSource !== "USER_INTERACTION") {
            return;
        }
        event.preventDefault();
        const edge = event.detail.edge as ItemRelationEdge;
        if (edge.deleteAction != null) {
            this.api.submitByApiLink<ChangedApiObject>(edge.deleteAction).then(result => {
                if (!isChangedApiObject(result.data)) {
                    console.error("Got wrong response type from API.");
                    return;
                }
                if (apiLinkToId(result.data.changed) === edge.id) {
                    this.graph.removeEdge(edge.id);
                    this.graph.completeRender();
                } else {
                    console.error("Unexpected change object from API!");
                }
                const promises = [];
                result.links.forEach(link => {
                    if (link.resourceType !== "ont-taxonomy-item") {
                        return;
                    }
                    // reload changed taxonomy items
                    const promise = this.api.getByApiLink<TaxonomyApiObject>(link).then(itemResult => {
                        const nodeId = apiLinkToId(itemResult.data.self);
                        const itemNode = this.graph.getNode(nodeId);
                        if (itemNode != null) {
                            itemNode.data = itemResult;
                        }
                    });
                    promises.push(promise);
                });
                Promise.all(promises).then(() => {
                    this.graph.completeRender();
                    this.layout();
                });
            });
        }
    }

    detached() {
        this.subscription?.dispose();
    }
}
