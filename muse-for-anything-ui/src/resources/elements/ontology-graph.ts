import { bindable, autoinject, observable, child } from "aurelia-framework";
import { EventAggregator, Subscription } from "aurelia-event-aggregator";
import { BaseApiService } from "rest/base-api";
import { ApiLink, ApiObject } from "rest/api-objects";
import { NavigationLinksService, NavLinks } from "services/navigation-links";
import { NAV_LINKS_CHANNEL } from "resources/events";
import GraphEditor from "@ustutt/grapheditor-webcomponent/lib/grapheditor";
import { Node } from "@ustutt/grapheditor-webcomponent/lib/node";
import { Point } from "@ustutt/grapheditor-webcomponent/lib/edge";
import { TaxonomyApiObject, TaxonomyItemApiObject, TaxonomyItemRelationApiObject } from "./taxonomy-graph";
import { GroupBehaviour, GroupingManager } from "@ustutt/grapheditor-webcomponent/lib/grouping";
import { DynamicNodeTemplate, DynamicTemplateContext } from "@ustutt/grapheditor-webcomponent/lib/dynamic-templates/dynamic-template";
import { LinkHandle } from "@ustutt/grapheditor-webcomponent/lib/link-handle";
import { Rect } from "@ustutt/grapheditor-webcomponent/lib/util";

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
            
            }| null
        },
        description: string | null;
        titel: string;
    };
}

class TaxonomyObject {
    name: string;
    href: string;
    description: string | null;
    itemsData: TaxonomyItemApiObject[];
}

class TypeItemNode implements DynamicNodeTemplate {

    getLinkHandles(g: Node, grapheditor: GraphEditor): LinkHandle[] {
            
        return;
        //throw new Error("Method not implemented.");
    }

    renderInitialTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        this.calculateRect(g,grapheditor,context,false);
    }

    updateTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        this.calculateRect(g,grapheditor,context, true);        
    }

    private calculateRect(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>, updated?:boolean) {
        let props = g._groups[0][0].__data__;
        const children = grapheditor.groupingManager.getAllChildrenOf(props.id);
        const boxes: Rect[] = [];
        children.forEach(childId => {
            const node = grapheditor.getNode(childId);
            const bbox = grapheditor.getNodeBBox(childId);
            
            boxes.push({
                x: node.x,
                y: node.y,
                width: bbox.width,
                height: bbox.height,
            });
        });

        const minBox = calculateBoundingRect(...boxes);
        minBox.width = Math.max(160,minBox.width);
        minBox.height = Math.max(80,minBox.height);

        this.drawRect(g, minBox,props);
    }

    private drawRect(g: any,minBox: any,props: any) {
        g.selectAll("*").remove();
        g.append("rect")
            .attr("width", minBox.width)
            .attr("height", minBox.height+20)
            .attr("class","ghost")
            .attr("rx",0);
        g.append("text")
            .attr("x", 5)
            .attr("y", 15)
            .attr('data-content', 'title');
        
    }

}

class TaxonomyGroupItemNode implements DynamicNodeTemplate {

    getLinkHandles(g: Node, grapheditor: GraphEditor): LinkHandle[] {
            
        return;
        //throw new Error("Method not implemented.");
    }

    renderInitialTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        this.calculateRect(g,grapheditor,context,false);
    }

    updateTemplate(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>): void {
        this.calculateRect(g,grapheditor,context, true);        
    }

    private calculateRect(g: any, grapheditor: GraphEditor, context: DynamicTemplateContext<Node>, updated?:boolean) {
        let props = g._groups[0][0].__data__;
        const children = grapheditor.groupingManager.getAllChildrenOf(props.id);
        const boxes: Rect[] = [];
        children.forEach(childId => {
            const node = grapheditor.getNode(childId);
            const bbox = grapheditor.getNodeBBox(childId);
            
            boxes.push({
                x: node.x,
                y: node.y,
                width: bbox.width,
                height: bbox.height,
            });
        });

        const minBox = calculateBoundingRect(...boxes);
        minBox.width = Math.max(160,minBox.width);
        minBox.height = Math.max(80,minBox.height);

        this.drawRect(g, minBox,props);
    }

    private drawRect(g: any,minBox: any,props: any) {
        g.selectAll("*").remove();
        g.append("rect")
            .attr("width", minBox.width)
            .attr("height", minBox.height+20)
            .attr("class","ghost")
            .attr("rx",0);
        g.append("text")
            .attr("x", 5)
            .attr("y", 15)
            .attr('data-content', 'title');
        
    }

}

class OverviewGraphNode implements DynamicNodeTemplate {
    
    getLinkHandles(g: Node, grapheditor: GraphEditor): LinkHandle[] {
        
        return;
        //throw new Error("Method not implemented.");
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

    private drawRect(g: any,props: any) {
        g.append("rect")
            .attr("width", props.width)
            .attr("height", props.height)
            .attr("x",0)
            .attr("y",0)
            .attr("class",props.class)
            .attr("rx",0);;
    }
}

class TaxonomyGroupBehaviour implements GroupBehaviour {
    moveChildrenAlongGoup = true;
    captureDraggedNodes = false;
    allowFreePositioning = true;
    allowDraggedNodesLeavingGroup = false;

    afterNodeJoinedGroup(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor, atPosition?: Point) {
        this.reposition(group, groupNode, graphEditor);
    }

    onNodeMoveEnd(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor) {
        this.reposition(group, groupNode, graphEditor);
    }

    reposition(group: string, groupNode: Node, graphEditor: GraphEditor) {
        const children = graphEditor.groupingManager.getAllChildrenOf(group);

        const boxes: Rect[] = [];
        children.forEach(childId => {
            const node = graphEditor.getNode(childId);
            const bbox = graphEditor.getNodeBBox(childId);
            boxes.push({
                x: node.x,
                y: node.y,
                width: bbox.width,
                height: bbox.height,
            });
        });


        const minBox = calculateBoundingRect(...boxes);

        // set config moveChildrenAlongGoup to false, to position group node around children, and set config back
        const tempConfig = graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup;
        graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup = false;
        graphEditor.moveNode(groupNode.id,minBox.x,minBox.y-minBox.height/2-20, false);
        graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup = tempConfig;

        graphEditor.completeRender(); // FIXME remove if no longer needed
    }
}

class TypeGroupBehaviour implements GroupBehaviour {
    moveChildrenAlongGoup = true;
    captureDraggedNodes = false;
    allowFreePositioning = true;
    allowDraggedNodesLeavingGroup = false;

    afterNodeJoinedGroup(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor, atPosition?: Point) {
        this.reposition(group, groupNode, graphEditor);
    }

    onNodeMoveStart(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor) {
        this.reposition(group, groupNode, graphEditor);
    }

    onNodeMoveEnd(group: string, childGroup: string, groupNode: Node, childNode: Node, graphEditor: GraphEditor) {
        this.reposition(group, groupNode, graphEditor);
    }

    reposition(group: string, groupNode: Node, graphEditor: GraphEditor) {
        const children = graphEditor.groupingManager.getAllChildrenOf(group);

        const boxes: Rect[] = [];
        children.forEach(childId => {
            const node = graphEditor.getNode(childId);
            const bbox = graphEditor.getNodeBBox(childId);
            boxes.push({
                x: node.x,
                y: node.y,
                width: bbox.width,
                height: bbox.height,
            });
        });


        const minBox = calculateBoundingRect(...boxes);

        // set config moveChildrenAlongGoup to false, to position group node around children, and set config back
        const tempConfig = graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup;
        graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup = false;
        graphEditor.moveNode(groupNode.id,minBox.x,minBox.y-minBox.height/2-20, false);
        graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup = tempConfig;

        graphEditor.completeRender(); // FIXME remove if no longer needed
    }
}

function calculateBoundingRect(...rectangles: Rect[]): Rect {
    const minBox={left:null, right:null, up:null,down:null}
    rectangles.forEach(box => {
        if(minBox.left == null || box.x - box.width/2 < minBox.left) {
            minBox.left = box.x - box.width/2;
        }
        if(minBox.right == null || box.x + box.width/2 > minBox.right) {
            minBox.right = box.x + box.width/2;
        }
        if(minBox.up == null || box.y - box.height/2 < minBox.up) {
            minBox.up = box.y - box.height/2;
        }
        if(minBox.down == null || box.y + box.height/2 > minBox.down) {
            minBox.down = box.y + box.height/2;
        }
    });

    return {x: minBox.left, y: minBox.down-(minBox.down-minBox.up)/2,width: minBox.right-minBox.left, height: minBox.down-minBox.up};
}

@autoinject
export class OntologyGraph {
    @bindable apiLink;
    @bindable ignoreCache = true;
    @bindable maximizeMenu = false;


    @child("network-graph.maingraph") graph: GraphEditor;
    @observable graphoverview: GraphEditor;
    @child("div.maindiv") maindiv: any;

    maximized: boolean = false;
    isLoggedIn: boolean = false;
    speed: number = 10; // pixels to move the nodes in the graph on interaction

    @observable() searchtext: String = "";
    @observable() selectedNode: Node;

    @observable() typeItems : Array<TypeItemApiObject> = [];
    @observable() taxonomyItems : Array<TaxonomyObject> = [];

    private api: BaseApiService;
    private navService: NavigationLinksService;
    private events: EventAggregator;

    private subscription: Subscription;

    constructor(baseApi: BaseApiService, navService: NavigationLinksService, events: EventAggregator) {
        this.api = baseApi;
        this.navService = navService;
        this.checkNavigationLinks();
        this.events = events;
        this.subscribe();
    }   

    apiLinkChanged(newValue: ApiLink, oldValue) {
        if (newValue == null) {
            return;
        }
        if(this.graph!=null) {
            this.loadData(this.apiLink, this.ignoreCache);
        }
    }

    maindivChanged(newValue: any, oldValue) {
        // need div, to get access to the graph overview part
        if (newValue == null) {
            return;
        }

        if(newValue.getElementsByClassName("graphoverview").length>0){
            this.graphoverview = newValue.getElementsByClassName("graphoverview")[0]
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
        
        newGraph.dynamicTemplateRegistry.addDynamicTemplate('type-group-node-template',new TypeItemNode);
        newGraph.dynamicTemplateRegistry.addDynamicTemplate('taxonomy-group-node-template',new TaxonomyGroupItemNode);
        
        if(this.apiLink!=null) {
            this.loadData(this.apiLink, this.ignoreCache);
        }
    }

    graphoverviewChanged(newGraph: GraphEditor, oldGraph) {
        if (newGraph == null) {
            return;
        }
        newGraph.dynamicTemplateRegistry.addDynamicTemplate('overview-node-template',new OverviewGraphNode);
    }

    searchtextChanged(newText: String, old) {
        if(this.graph==null) {
            return;
        }
        if(newText=="") {
            this.graph.changeSelected(null);
        } else {
            this.graph.nodeList.forEach(node => {
                if(node.title.startsWith(newText)) {
                    this.graph.selectNode(node.id);
                } else {
                    this.graph.deselectNode(node.id);
                }
            });
        }
        this.graph.updateHighlights();
    }
    
    typeItemsChanged(newItem, oldItem) {
        this.finishDataLoading();
    }

    taxonomyItemsChanged(newItem, oldItem) {
        this.finishDataLoading();
    }

    private subscribe() {
        this.subscription = this.events.subscribe(NAV_LINKS_CHANNEL, (navLinks: NavLinks) => {
            this.checkNavigationLinks();
        });
    }

    private checkNavigationLinks() {
        if (true && this.navService.getCurrentNavLinks().nav?.length > 0) {
            if (this.navService.getCurrentNavLinks().nav.some(link => link.apiLink.resourceType == "ont-taxonomy") && 
            this.navService.getCurrentNavLinks().nav.some(link => link.apiLink.resourceType == "ont-type")) 
            {
                this.isLoggedIn = true;
            } else {
                this.isLoggedIn = false;
            }
        }
    }

    private loadData(apiLink: ApiLink, ignoreCache: boolean) {
        console.log("load data")
        this.loadDataTaxonomy(apiLink.href, this.ignoreCache);
        this.loadDataTypes(apiLink.href, this.ignoreCache);
        
    }

    private finishDataLoading() {
        this.renderGraph();
    }

    private loadDataTypes(linkNamespace: String, ignoreCache: boolean) {
        const promises = [];
        let typesRootLink :ApiLink = {href: linkNamespace + "types/", rel: null, resourceType: null};
        const promise = this.api.getByApiLink<TypeApiObject>(typesRootLink, ignoreCache).then(apiResponse => {
            // for each type in namespace
            apiResponse.data.items?.forEach(element => {
                // load each type of the namespace
                const promiseInner = this.api.getByApiLink<TypeItemApiObject>(element, ignoreCache).then(apiResponse => {
                    this.typeItems.push(apiResponse.data);
                });
                promises.push(promiseInner);
            });
        });
        Promise.all(promises).then(() => {
            console.log("done with all type data")
            this.finishDataLoading();
        });
    }

    private loadDataTaxonomy(linkNamespace: String, ignoreCache: boolean) {
        const groupingManager = this.graph.groupingManager;
        const promises = [];
        let newlink :ApiLink = {href: linkNamespace + "taxonomies/", rel: null, resourceType: null};
        const promise = this.api.getByApiLink<TaxonomyApiObject>(newlink, ignoreCache).then(apiResponse => {
            // for each taxonomy in namespace
            apiResponse.data.items.forEach(element => {
                const promiseInner = this.api.getByApiLink<TaxonomyApiObject>(element, ignoreCache).then(apiResponse => {
                    let taxonomie : Array<TaxonomyItemApiObject> = [];
                    apiResponse.data.items.forEach(element => {
                        this.api.getByApiLink<TaxonomyItemApiObject>(element, ignoreCache).then(apiResponse => {
                            taxonomie.push(apiResponse.data);
                        });
                    });
                    let taxItem : TaxonomyObject = {
                        description: apiResponse.data.description,
                        href: apiResponse.data.self.href,
                        name: apiResponse.data.name,
                        itemsData: taxonomie,
                    };
                    this.taxonomyItems.push(taxItem)
                });
                promises.push(promiseInner);
            });
        });
        Promise.all(promises).then(() => {
            console.log("done with all tax data")
            this.finishDataLoading();
        });
    }


    private renderGraph() {
        if(this.graph == null){
            return;
        }
        const groupManager = this.graph.groupingManager;

        this.typeItems.forEach(element => {
            let parentID =  this.addNodeToGraph({id: element.self.href, title: element.name, dynamicTemplate:"type-group-node-template", x:Math.random()*1000,y:Math.random()*1000});
            if(parentID!=null)
            {
                groupManager.markAsTreeRoot(parentID);
                groupManager.setGroupBehaviourOf(parentID, new TypeGroupBehaviour());
            }
            if(element.schema.definitions?.root?.properties == null) {
                return;
            }
            console.log(element.schema.definitions?.root?.properties)
            let posX = 80;
            let counter = 0;
            for (let typeElement in element.schema.definitions?.root?.properties) {  
                let typeProps = element.schema.definitions?.root?.properties[typeElement];
                let nodeID;
                if(typeProps["type"]=="object") {
                    if(typeProps["referenceType"]=="ont-taxonomy") {
                        let taxonomoyHref = this.getTaxonomyHref(typeProps["referenceKey"]["namespaceId"],typeProps["referenceKey"]["taxonomyId"])
                        
                        nodeID = this.addTaxonomyItem(this.taxonomyItems.find(f => f.href == taxonomoyHref).itemsData,groupManager);
                        console.log("added taxonomy to type: ", nodeID)
                    } else {
                        nodeID = this.addNodeToGraph({id: parentID+typeElement, title: typeElement, type: typeProps["referenceType"], x:Math.floor(counter/2)*150,y:posX});
                    }
                } else {
                    console.log("Type:" , typeProps["type"])
                    if(typeProps["type"] == "string" || 
                    typeProps["type"] == "integer" ){
                        nodeID = this.addNodeToGraph({id: parentID+typeElement, title: typeProps["type"] + " " + typeElement, type: "taxonomy-item", x:Math.floor(counter/2)*150,y:posX});
                    }   
                    else {
                        nodeID = this.addNodeToGraph({id: parentID+typeElement, title: typeElement, type: typeProps["type"], x:Math.floor(counter/2)*150,y:posX});
                    }
                    
                }
                console.log((counter%2)*150,posX);
                if(nodeID != null) {
                    groupManager.addNodeToGroup(parentID, nodeID);
                    groupManager.joinTreeOfParent(nodeID,parentID); //WHY???
                }
                posX = posX*-1;
                counter++;
            }  
        });

        this.taxonomyItems.forEach((element) => {
            this.addTaxonomyItem(element.itemsData,groupManager);
        });

        this.graph.completeRender();
        this.graph?.zoomToBoundingBox();
    }

    private getTaxonomyHref(namespaceId: number, taxonomyID: number): string {
        return "http://localhost:5000/api/v1/namespaces/"+namespaceId+"/taxonomies/"+taxonomyID+"/";
    }

    private addTaxonomyItem(element: TaxonomyItemApiObject[], groupManager: GroupingManager):string|number {
        let firstItem = true;
        let parentPosition: {x,y}
        let parentID: number|string;
        let childElements: Array<{href:string,id:number|string}> = []
        element.forEach(childElement => {
            if(firstItem) {
                parentPosition = {x:1000+Math.random()*1000,y:1000+Math.random()*1000}
                parentID = this.addNodeToGraph({id: childElement.self.href+"boundingBox", title: childElement.name, dynamicTemplate:"taxonomy-group-node-template",...parentPosition});
                if(parentID != null) 
                {
                    groupManager.markAsTreeRoot(parentID);
                    groupManager.setGroupBehaviourOf(parentID, new TaxonomyGroupBehaviour());
                    firstItem = false;
                }
            } 

            let nodeID = this.addNodeToGraph({id: childElement.self.href, title: childElement.name, type: 'taxonomy-item', x:parentPosition.x+Math.random()*100,y:parentPosition.y+Math.random()*100});
            childElements.push({href:childElement.self.href,id:nodeID});
            if(nodeID != null) 
            {
                groupManager.addNodeToGroup(parentID, nodeID);
            }
        });

        element.forEach(parentElement => {
            parentElement.children.forEach(childElement => {
                this.api.getByApiLink<TaxonomyItemRelationApiObject>(childElement, true).then(apiResponse => {
                    let source = childElements.find(e => e.href == apiResponse.data.sourceItem.href);
                    let target = childElements.find(e => e.href == apiResponse.data.targetItem.href);
                    let path = {source: source.id, target: target.id,markerEnd : {
                        template: "default-marker",
                        scale: 0.8,
                        relativeRotation: 0,
                    }}
                    this.graph.addEdge(path,true)
                });
            });
        })

        return parentID;
    }

    // add a new node to both graphs, if the node isn't already there
    private addNodeToGraph(node: Node): string {
        node.id = String(node.id).replace(RegExp(/\/\/|\/|:| /g),"")
        node.id = node.id + Math.floor(Math.random()*10000000000000);
        node.id = String(Math.floor(Math.random()*100000000000000000000));
        
        if(this.graph.nodeList.some(element => element.id == node.id)){
            throw new Error("Item already exists in graph: "+ node.id);
        }
        this.graph?.addNode(node,true);
        this.graphoverview?.addNode(node,true);

        return node.id;
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
        this.selectedNode = node;
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
        this.renderMainViewPositionInOverview();
    }

    private onNodeAdd(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node }>) {
        let currentView = this.graph.currentViewWindow;
        this.graphoverview.removeNode(42424242424242424242424242424242421,false);
        this.graphoverview.addNode({id:42424242424242424242424242424242421,class:"", dynamicTemplate:'overview-node-template',x:currentView.x,y:currentView.y,width:currentView.width,height:currentView.height},true);
    }

    private onZoomChange(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node }>) {
        this.renderMainViewPositionInOverview();
    }

    private renderMainViewPositionInOverview() {
        let currentView = this.graph.currentViewWindow;
        this.graphoverview.removeNode(4242424242424242424242424242424242,false);
        this.graphoverview.addNode({id:4242424242424242424242424242424242,class:"position-rect", dynamicTemplate:'overview-node-template',x:currentView.x,y:currentView.y,width:currentView.width,height:currentView.height},true);
    }    

    // function called by buttons from the front-end, to interact with the graph
    private zoomIn() {
        let zoomBox =  this.graph.currentViewWindow;
        let newBox: Rect = {x:0,y:0,width:0,height:0};
        newBox.width = zoomBox.width-zoomBox.width*0.2;
        newBox.height = zoomBox.height-zoomBox.height*0.2;
        newBox.x = zoomBox.x+(zoomBox.width-newBox.width)*0.5;
        newBox.y = zoomBox.y+(zoomBox.height-newBox.height)*0.5;
        this.graph.zoomToBox(newBox);
    }

    // function called by buttons from the front-end, to interact with the graph
    private zoomOut() {
        let zoomBox =  this.graph.currentViewWindow;
        let newBox: Rect = {x:0,y:0,width:0,height:0};
        newBox.width = zoomBox.width+zoomBox.width*0.2;
        newBox.height = zoomBox.height+zoomBox.height*0.2;
        newBox.x = zoomBox.x+(zoomBox.width-newBox.width)*0.5;
        newBox.y = zoomBox.y+(zoomBox.height-newBox.height)*0.5;
        this.graph.zoomToBox(newBox);
    }

    // function called by buttons from the front-end, to interact with the graph
    private toggleMaximize() {
        this.maximized = !this.maximized;
    }

    // function called by buttons from the front-end, to interact with the graph
    private toggleMenu() {
        this.maximizeMenu = !this.maximizeMenu;
        this.finishDataLoading();
    }

    // function called by buttons from the front-end, to interact with the graph
    private resetLayout() {
        this.graph?.zoomToBoundingBox(true);
    }

    // function called by buttons from the front-end, to interact with the graph
    private moveGraph(direction: String) {
        let dirX = 0;
        let dirY = 0;
        
        if(direction=='up') {
            dirY = -this.speed;
        } else if(direction=='left') {
            dirX = -this.speed;
        } else if(direction=='right') {
            dirX = this.speed;
        } else if(direction=='down') {
            dirY = this.speed;
        } 

        this.graph.nodeList.forEach(node => {
            this.graph.moveNode(node.id, node.x+dirX, node.y+dirY, false);
        })

        this.graph.completeRender();
    }
}
