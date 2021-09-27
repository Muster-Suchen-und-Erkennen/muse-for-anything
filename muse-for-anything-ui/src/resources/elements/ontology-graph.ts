import { bindable, autoinject, observable, child } from "aurelia-framework";
import {BindingEngine} from 'aurelia-framework';
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

interface TypeApiObject extends ApiObject {
    collectionSize: number;
    items: ApiLink[];
    page: number;
}

const boundingBoxTaxonomyMarker: string = "boundingBoxTaxonomyMarker";
const boundingBoxBorder: number = 20;

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
        throw new Error("Method not implemented.");
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
        if(children.size==0) {
            return;
        }
        const boxes: Rect[] = [];
        children.forEach(childId => {
            
            const node = grapheditor.getNode(childId);
            const bbox = grapheditor.getNodeBBox(childId);
            console.log(node, bbox)
            
            if(childId.includes(boundingBoxTaxonomyMarker)) {
                boxes.push({
                    x: node.x+bbox.x,
                    y: node.y+bbox.y,
                    width: bbox.width,
                    height: bbox.height,
                });
            } else {
                boxes.push({
                    x: node.x+bbox.x,
                    y: node.y+bbox.y,
                    width: bbox.width,
                    height: bbox.height,
                });
            }

            
        });

        console.log("bxos", boxes)
        const minBox = calculateBoundingRect(...boxes);
        minBox.width = Math.max(160,minBox.width);
        minBox.height = Math.max(80,minBox.height);

        this.drawRect(g, minBox,props);
    }

    private drawRect(g: any,minBox: any,props: any) {
        g.selectAll("*").remove();
        g.append("rect")
            .attr("width", minBox.width+boundingBoxBorder*2)
            .attr("height", minBox.height+boundingBoxBorder*2)
            .attr("class","type-group")
            .attr("rx",5);
        g.append("text")
            .attr("x", 5)
            .attr("y", 15)
            .attr('data-content', 'title');
        
    }

}

class TaxonomyGroupItemNode implements DynamicNodeTemplate {
    
    getLinkHandles(g: any, grapheditor: GraphEditor): LinkHandle[] {
        return;
        throw new Error("Method not implemented.");
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
                x: node.x+bbox.x,
                y: node.y+bbox.y,
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
            .attr("width", minBox.width+boundingBoxBorder*2)
            .attr("height", minBox.height+boundingBoxBorder*2)
            .attr("class","taxonomy-group")
            .attr("rx",5);
        g.append("text")
            .attr("x", 5)
            .attr("y", 15)
            .attr('data-content', 'title');
        
    }

}

class OverviewGraphNode implements DynamicNodeTemplate {
    
    getLinkHandles(g: any, grapheditor: GraphEditor): LinkHandle[] {
        return;
        throw new Error("Method not implemented.");
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
            .attr("rx",0);
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
                x: node.x+bbox.x,
                y: node.y+bbox.y,
                width: bbox.width,
                height: bbox.height,
            });
        });


        const minBox = calculateBoundingRect(...boxes);

        // set config moveChildrenAlongGoup to false, to position group node around children, and set config back
        const tempConfig = graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup;
        graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup = false;
        graphEditor.moveNode(groupNode.id,minBox.x-boundingBoxBorder,minBox.y-boundingBoxBorder, false);
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
            if(childId.includes(boundingBoxTaxonomyMarker)) {
                boxes.push({
                    x: node.x+bbox.x,
                    y: node.y+bbox.y,
                    width: bbox.width,
                    height: bbox.height,
                });
            } else {
                boxes.push({
                    x: node.x+bbox.x,
                    y: node.y+bbox.y,
                    width: bbox.width,
                    height: bbox.height,
                });
            }
        });

        const minBox = calculateBoundingRect(...boxes);

        // set config moveChildrenAlongGoup to false, to position group node around children, and set config back
        const tempConfig = graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup;
        graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup = false;
        graphEditor.moveNode(groupNode.id,minBox.x-boundingBoxBorder,minBox.y-boundingBoxBorder, false);
        graphEditor.groupingManager.getGroupBehaviourOf(groupNode.id).moveChildrenAlongGoup = tempConfig;

        graphEditor.completeRender(); // FIXME remove if no longer needed
    }
}

@autoinject
export class OntologyGraph {
    @bindable apiLink;
    @bindable ignoreCache = false;
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

    constructor(baseApi: BaseApiService, navService: NavigationLinksService, events: EventAggregator, bindingEngine: BindingEngine) {
        this.api = baseApi;
        this.navService = navService;
        this.checkNavigationLinks();
        this.events = events;
        this.subscribe();


      bindingEngine.collectionObserver(this.typeItems)
      .subscribe(this.typeItemsChanged.bind(this));


      bindingEngine.collectionObserver(this.taxonomyItems)
        .subscribe(this.taxonomyItemsChanged.bind(this));
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
    
    typeItemsChanged(newItem) {
        if(newItem.length != 0) {

            //this.addTypeItem(this.typeItems[newItem[0].index]);
        }
    }

    taxonomyItemsChanged(newItem) {
        if(newItem.length != 0) {
            //this.addTaxonomyItem(this.taxonomyItems[newItem[0].index],{x:0,y:0});
        }
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

        this.typeItems.forEach(element => {
             this.addTypeItem(element,{x:null,y:null});
        });

        this.taxonomyItems.forEach((element) => {
            this.addTaxonomyItem(element,{x:0,y:0});
        });

        this.graph.completeRender();
        this.graph?.zoomToBoundingBox();
    }

    private addTypeItem(element: TypeItemApiObject, parentPosition: {x,y}):{id:string|number, bbox: Rect} {
        parentPosition.x = parentPosition.x+20;
        parentPosition.y = parentPosition.y+20;
        let groupManager = this.graph.groupingManager;
        let parPos = {x:parentPosition.x,y:parentPosition.y};
        let parentID =  this.addNodeToGraph({id: element.self.href, title: element.name, dynamicTemplate:"type-group-node-template", ...parPos});
        if(parentID.id!=null)
        {
            groupManager.markAsTreeRoot(parentID.id);
            groupManager.setGroupBehaviourOf(parentID.id, new TypeGroupBehaviour());
        }
        if(element.schema.definitions?.root?.properties == null) {
            return;
        }
        let nodeID: {id:string|number, bbox: Rect} = {id:null, bbox:{x:parentID.bbox.x,y:parentID.bbox.y,width:parentID.bbox.width,height:parentID.bbox.height}};
        for (let typeElement in element.schema.definitions?.root?.properties) {  
            let typeProps = element.schema.definitions?.root?.properties[typeElement];
            if(typeProps["type"]=="object") {
                if(typeProps["referenceType"]=="ont-taxonomy") {
                    let taxonomoyHref = this.getTaxonomyHref(typeProps["referenceKey"]["namespaceId"],typeProps["referenceKey"]["taxonomyId"])
                    if(this.taxonomyItems.some(f => f.href == taxonomoyHref)){
                        nodeID = this.addTaxonomyItem(this.taxonomyItems.find(f => f.href == taxonomoyHref),{x:nodeID.bbox.x,y:nodeID.bbox.y});
                    }else {
                        nodeID.id = null;
                    }
                } else if(typeProps["referenceType"]=="ont-type") {
                    let typeHref = this.getTypeHref(typeProps["referenceKey"]["namespaceId"],typeProps["referenceKey"]["typeId"])
                    console.log(typeHref, this.typeItems)
                    if(this.typeItems.some(f => f.self.href == typeHref)){
                        console.log("add type", this.typeItems.find(f => f.self.href == typeHref))
                        nodeID = this.addTypeItem(this.typeItems.find(f => f.self.href == typeHref),{x:nodeID.bbox.x,y:nodeID.bbox.y});
                    } else {
                        nodeID.id = null;
                    }
                } else {
                    console.log("Undefined Object found: " , typeProps["referenceType"])
                    nodeID = this.addNodeToGraph({id: parentID.id+typeElement, title: typeElement, type: typeProps["referenceType"], x:nodeID.bbox.x,y:nodeID.bbox.y});
                }
            } else if(typeProps["enum"] ) {
                nodeID = this.addNodeToGraph({id: parentID.id+typeElement, title: "enum" + " " + typeElement, type: "taxonomy-item", x:nodeID.bbox.x,y:nodeID.bbox.y});
            } else {
                console.log("Type:" , typeProps)
                if(typeProps["type"] == "string" || 
                    typeProps["type"] == "integer" || 
                    typeProps["type"] == "boolean" || 
                    typeProps["type"] == "number" ){
                    nodeID = this.addNodeToGraph({id: parentID.id+typeElement, title: typeProps["type"] + " " + typeElement, type: "taxonomy-item", x:nodeID.bbox.x,y:nodeID.bbox.y});
                }   
                else {
                    nodeID = this.addNodeToGraph({id: parentID.id+typeElement, title: typeElement, type: typeProps["type"], x:nodeID.bbox.x,y:nodeID.bbox.y});
                }
                
            }
            if(nodeID.id != null) {
                groupManager.addNodeToGroup(parentID.id, nodeID.id);
                groupManager.joinTreeOfParent(nodeID.id,parentID.id); //WHY???
            }
        } 
        this.graph.completeRender();
        return {id: parentID.id, bbox: this.getBoundingBoxOfItem(this.graph.getNode(parentID.id))};
    }

    private getTaxonomyHref(namespaceId: number, taxonomyID: number): string {
        return "http://localhost:5000/api/v1/namespaces/"+namespaceId+"/taxonomies/"+taxonomyID+"/";
    }
    private getTypeHref(namespaceId: number, typeID: number): string {
        return "http://localhost:5000/api/v1/namespaces/"+namespaceId+"/types/"+typeID+"/";
    }

    private addTaxonomyItem(element: TaxonomyObject, parentPosition: {x,y}):{id:string|number, bbox: Rect} {
        parentPosition.x = parentPosition.x+20;
        parentPosition.y = parentPosition.y+20;
        let groupManager = this.graph.groupingManager;
        let firstItem = true;
        let parentID: {id:string|number, bbox: Rect};
        let yPosition = 40;
        let childElements: Array<{href:string,id:number|string}> = []
        element.itemsData.forEach(childElement => {
            if(firstItem) {
                parentID = this.addNodeToGraph({id: element.href+boundingBoxTaxonomyMarker, title: element.name, dynamicTemplate:"taxonomy-group-node-template",...parentPosition});
                if(parentID != null) 
                {
                    groupManager.markAsTreeRoot(parentID.id);
                    groupManager.setGroupBehaviourOf(parentID.id, new TaxonomyGroupBehaviour());
                    firstItem = false;
                }
            } 
            let nodeID = this.addNodeToGraph({id: childElement.self.href, title: childElement.name, type: 'taxonomy-item', x:parentPosition.x+Math.floor(childElements.length/2)*150,y:parentPosition.y+40-yPosition});
            yPosition = yPosition*-1;
            childElements.push({href:childElement.self.href,id:nodeID.id});
            if(nodeID != null) 
            {
                groupManager.addNodeToGroup(parentID.id, nodeID.id);
            }
        });

        element.itemsData.forEach(parentElement => {
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
        this.graph.completeRender();

        return {id: parentID.id, bbox: this.getBoundingBoxOfItem(this.graph.getNode(parentID.id))};
    }

    // add a new node to both graphs, if the node isn't already there
    private addNodeToGraph(node: Node): {id:string|number, bbox: Rect} {
        node.id = String(node.id).replace(RegExp(/\/\/|\/|:| /g),"")
        node.id = node.id + Math.floor(Math.random()*10000000000000);


        if(node.type) {
            //console.log("template",this.graph.staticTemplateRegistry.getNodeTemplate(node.type));
            //120x60
            node.x = node.x+60;
            node.y = node.y+30;
        }
        
        if(this.graph.nodeList.some(element => element.id == node.id)){
            throw new Error("Item already exists in graph: "+ node.id);
        }
        this.graph?.addNode(node,true);
        this.graphoverview?.addNode(node,true);

        return {id: node.id, bbox: this.getBoundingBoxOfItem(node)};
    }

    private getBoundingBoxOfItem(node: Node): Rect {
        const bbox = this.graph.getNodeBBox(node.id);
        const boxes: Rect[] = [];
        boxes.push({
            x: bbox.x+node.x,
            y: bbox.y+node.y,
            width: bbox.width,
            height: bbox.height,
        });
        let tempRect = calculateBoundingRect(...boxes);

        // TODO: settings 10 distance to other box
        return {x:tempRect.x,y:tempRect.y+tempRect.height+10,height:tempRect.height,width:tempRect.width}
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