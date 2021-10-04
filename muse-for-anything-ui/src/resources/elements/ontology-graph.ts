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


const taxonomyGroupIdMarker: string = "boundingBoxTaxonomyMarker";
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
            
            }| null
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
            boxes.push({
                x: node.x+bbox.x,
                y: node.y+bbox.y,
                width: bbox.width,
                height: bbox.height,
            });
        });

        const minBox = calculateMinBoundingRect(boxes);

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
            .attr("class", "title")
            .attr("width", minBox.width+boundingBoxBorder*2-5)
            .attr('data-content', 'title');
    }
}

function calculateMinBoundingRect(boxes:Rect[]):Rect {
    const minBox = calculateBoundingRect(...boxes);
    minBox.width = Math.max(160,minBox.width);
    minBox.height = Math.max(80,minBox.height);
    return minBox;
}

export class ListNodeModel {
    public id: Node;
    public name: string;
    public icon: string;
    public children: ListNodeModel[];
    public expanded: boolean;
    public visible: boolean;
    private graph: GraphEditor;
    @observable() isSelected: boolean;
   
    constructor(graph: GraphEditor, idVal: Node,name: string, visible: boolean, children: ListNodeModel[]) {
      this.id = idVal;
      this.name = name;
      this.visible = visible;
      this.children = children || [];
      this.graph = graph;
   
      if (this.hasChildren()) {
        this.icon = "arrow-right";
        this.expanded = false;
      }
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

    isSelectedChanged(newValue,oldValue) {
        console.log(this.children)
        if (newValue === true) {
          this.graph.selectNode(this.id.id);
        } else {
          this.graph.deselectNode(this.id.id);
        }
        this.graph.updateHighlights();
    }

    addChild(childName: string,id: Node) {
        this.children.push(new ListNodeModel(this.graph,id,childName,false,null))
        this.icon = "arrow-right";
        this.expanded = false;
    }
  }

class TaxonomyNodeTemplate implements DynamicNodeTemplate {
    
    getLinkHandles(g: any, grapheditor: GraphEditor): LinkHandle[] {
        return;
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
            this.drawRect(g,{x:0,y:0,width:120,height:20},props,false)
            return;
        }

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

        let minBox = calculateMinBoundingRect(boxes);

        this.drawRect(g, minBox,props,true);
    }

    private drawRect(g: any,minBox: any,props: any,childsVisible:boolean) {
        g.selectAll("*").remove();
        g.append("rect")
            .attr("width", minBox.width+boundingBoxBorder*2)
            .attr("height", minBox.height+boundingBoxBorder*2)
            .attr("class","taxonomy-group")
            .attr("data-click","node")
            .attr("rx",5);
        g.append("text")
            .attr("x", 5)
            .attr("y", 15)
            .attr("class", "title")
            .attr("width", minBox.width+boundingBoxBorder*2-5)
            .attr("data-click","header")
            .attr('data-content', 'title');   

        // add + or - to node for collapsing details or not
        let collapseIconElement = g.append("g")
            .attr("transform","translate(5,20)")
            .attr("data-click","expandNode").attr("fill","white").attr("fill-rule","evenodd").attr("stroke","currentColor").attr("stroke-linecap","round").attr("stroke-linejoin","round")
        collapseIconElement.append("path").attr("d","m12.5 10.5v-8c0-1.1045695-.8954305-2-2-2h-8c-1.1045695 0-2 .8954305-2 2v8c0 1.1045695.8954305 2 2 2h8c1.1045695 0 2-.8954305 2-2z")
        collapseIconElement.append("path").attr("d","m6.5 3.5v6").attr("transform","matrix(0 1 -1 0 13 0)")

        if(!childsVisible) collapseIconElement.append("path").attr("d","m6.5 3.5v6.056")
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

    @observable() typeItems : Array<TypeItemApiObject> = [];
    @observable() taxonomyItems : Array<TaxonomyObject> = [];
    missingParentConnection: Array<{parent:number|string,child:number|string,joinTree:boolean}> = [];

    public nodes: ListNodeModel[] = [];

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

    private subscribe() {
        this.subscription = this.events.subscribe(NAV_LINKS_CHANNEL, (navLinks: NavLinks) => {
            this.checkNavigationLinks();
        });
    }

    // check if the user is allowed to see the ontology graph
    private checkNavigationLinks() {
        if (true && this.navService.getCurrentNavLinks().nav?.length > 0) {
            if (this.navService.getCurrentNavLinks().nav.some(link => link.apiLink.resourceType == "ont-taxonomy") && 
            this.navService.getCurrentNavLinks().nav.some(link => link.apiLink.resourceType == "ont-type")) 
            {
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
        this.loadData(this.apiLink, this.ignoreCache);
    }

    maindivChanged(newValue: any, oldValue) {
        // need div, to get access to the graph overview part
        if (newValue == null) {
            return;
        }

        if(newValue.getElementsByClassName("graphoverview").length>0){
            this.graphoverview = newValue.getElementsByClassName("graphoverview")[0]
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
        
        newGraph.dynamicTemplateRegistry.addDynamicTemplate('type-group-node-template',new TypeNodeTemplate);
        newGraph.dynamicTemplateRegistry.addDynamicTemplate('taxonomy-group-node-template',new TaxonomyNodeTemplate);
    }

    graphoverviewChanged(newGraph: GraphEditor, oldGraph) {
        if (newGraph == null) {
            return;
        }
        newGraph.dynamicTemplateRegistry.addDynamicTemplate('overview-node-template',new OverviewGraphNode);
        newGraph.dynamicTemplateRegistry.addDynamicTemplate('type-group-node-template',new TypeNodeTemplate);
        newGraph.dynamicTemplateRegistry.addDynamicTemplate('taxonomy-group-node-template',new TaxonomyNodeTemplate);
    }

    searchtextChanged(newText: string, old: string) {
        if(this.graph==null) {
            return;
        }
        if(newText=="") {
            this.graph.changeSelected(null);
        } else {
            this.graph.nodeList.forEach(node => {
                if(node.title.includes(newText)) {
                    this.graph.selectNode(node.id);
                } else {
                    this.graph.deselectNode(node.id);
                }
            });
        }
        
        this.recursiveListSearch(this.nodes,newText);

        this.graph.updateHighlights();
    }

    recursiveListSearch(items: ListNodeModel[], searchText: string) {
        items.forEach(item => {
            if (item.name.includes(searchText) && searchText!="") {
                item.isSelected = true;
            }
            else {
                item.isSelected = false;
            }
            this.recursiveListSearch(item.children,searchText)
        })
    }
    
    typeItemsChanged(newItem) {
        return;
        if(newItem.length != 0) {
            
            let pos = {x:Math.floor(Math.random()*1000),y:Math.floor(Math.random()*1000)}; 
            this.addTypeItem(this.typeItems[newItem[0].index],pos);
            this.graph.completeRender();
            this.addChildnodesToParents();
            this.addHiddenLinks();
        }
    }

    taxonomyItemsChanged(newItem) {
        return;
        if(newItem.length != 0) {
            let pos = {x:Math.floor(Math.random()*1000),y:Math.floor(Math.random()*1000)}; 
            this.addTaxonomyItem(this.taxonomyItems[newItem[0].index],pos);
            this.graph.completeRender();
            this.addChildnodesToParents();
            this.addHiddenLinks();
        }
    }

    private loadData(apiLink: ApiLink, ignoreCache: boolean) {
        console.log("Start loading data")
        this.loadDataTaxonomy(apiLink.href+ "taxonomies/", this.ignoreCache);
        this.loadDataTypes(apiLink.href+ "types/", this.ignoreCache);
    }

    private finishDataLoading() {
        this.totalNodesToAdd = 0;
        this.totalNodesAdded = 0;
        this.taxonomyItems.forEach(tax => {this.totalNodesToAdd = this.totalNodesToAdd + tax.itemsData.length+1})
        this.typeItems.forEach(type => {
            this.totalNodesToAdd ++;
            if(type.schema.definitions?.root?.properties == null) {
                return;
            }
            for (let typeItems in type.schema.definitions?.root?.properties) { 
                this.totalNodesToAdd ++;
            }
        })
        this.isLoading=1;
        this.renderGraph();
    }

    private loadDataTypes(linkNamespace: string, ignoreCache: boolean) {
        // TODO: check promises
        const promises = [];
        let typesRootLink :ApiLink = {href: linkNamespace , rel: null, resourceType: null};
        const promise = this.api.getByApiLink<TypeApiObject>(typesRootLink, ignoreCache).then(apiResponse => {
            apiResponse.links.forEach(link=> {
                if(link.rel.includes("next")) {
                    this.loadDataTypes(link.href,this.ignoreCache);
                }
            })
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
            //this.finishDataLoading();
        });
    }

    private loadDataTaxonomy(linkNamespace: string, ignoreCache: boolean) {
        // TODO: check promises
        const promises = [];
        let newlink :ApiLink = {href: linkNamespace, rel: null, resourceType: null};
        const promise = this.api.getByApiLink<TaxonomyApiObject>(newlink, ignoreCache).then(apiResponse => {
            apiResponse.links.forEach(link=> {
                if(link.rel.includes("next")) {
                    this.loadDataTaxonomy(link.href,this.ignoreCache);
                }
            })
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
                        namespaceId:apiResponse.data.self.resourceKey.namespaceId,
                        taxonomyId:apiResponse.data.self.resourceKey.taxonomyId,
                        nodeId: null
                    };
                    this.taxonomyItems.push(taxItem)
                });
                promises.push(promiseInner);
            });
        });
        Promise.all(promises).then(() => {
            console.log("done with all tax data")
            //this.finishDataLoading();
        });
    }


    private async renderGraph() {
        let startTime = Date.now();
        if(this.graph == null){
            return;
        }

        await this.typeItems.forEach(element => {
            let pos = {x:Math.floor(Math.random()*1000),y:Math.floor(Math.random()*1000)}; 
            this.addTypeItem(element,pos);
        });

        await this.taxonomyItems.forEach((element) => {
            let pos = {x:Math.floor(Math.random()*1000),y:Math.floor(Math.random()*1000)}; 
            this.addTaxonomyItem(element,pos);
        });

        await this.graph.completeRender();

        await this.addChildnodesToParents();

        await this.addHiddenLinks();

        await this.graph.completeRender();

        await this.graph?.zoomToBoundingBox();

        this.isLoading=2;
    }

    private addHiddenLinks() {
        this.graph.nodeList.forEach(node => {
            console.log()
            if(node.id.toString().includes("childItem") && this.isNumber(node.id.toString().substr(node.id.toString().indexOf("childItem")+9))) {
                let target = this.graph.nodeList.find(tar => !tar.id.toString().includes("childItem") && tar.id.toString().startsWith(node.id.toString().substr(0,node.id.toString().indexOf("childItem"))))
                
                if(target) {    
                    let path = {source: node.id, target: target.id,markerEnd : {
                        template: "arrow",
                        scale: 0.8,
                        relativeRotation: 0,
                    }}
                    this.graph.addEdge(path,false)
                    this.graphoverview.addEdge(path,false)
                } else {
                    //throw new Error("Target for edge could not be found" + node.id)
                    console.log("Target for edge could not be found", node)
                }

            }
        })
    }

    private async addChildnodesToParents() {
        /*await this.missingParentConnection.forEach(node => {
            this.graph.groupingManager.addNodeToGroup(node.parent, node.child);
            if(node.joinTree) {
                this.graph.groupingManager.joinTreeOfParent(node.child,node.parent); //WHY???
            }
        });*/
        while(this.missingParentConnection.length!=0) {
            let node = this.missingParentConnection.pop();
            this.graph.groupingManager.addNodeToGroup(node.parent, node.child);
            if(node.joinTree) {
                this.graph.groupingManager.joinTreeOfParent(node.child,node.parent); //WHY???
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
        return "http://localhost:5000/api/v1/namespaces/"+namespaceId+"/taxonomies/"+taxonomyID+"/";
    }

    private getTypeHref(namespaceId: number, typeID: number): string {
        return "http://localhost:5000/api/v1/namespaces/"+namespaceId+"/types/"+typeID+"/";
    }

    private addTypeItem(typeMainObject: TypeItemApiObject, parentPosition: {x,y}):{id:Node, bbox: {x,y}} {
        parentPosition.x = parentPosition.x+boundingBoxBorder;
        parentPosition.y = parentPosition.y+boundingBoxBorder;
        let groupManager = this.graph.groupingManager;
        let parentID =  this.addNodeToGraph({id: typeMainObject.self.href, title: typeMainObject.name, dynamicTemplate:"type-group-node-template", ...parentPosition},true);

        this.nodes.push(new ListNodeModel(this.graph,parentID.id,typeMainObject.self.name,true,null))

        if(parentID.id==null) {
            return;
        }
           
        groupManager.markAsTreeRoot(parentID.id.id);
        groupManager.setGroupBehaviourOf(parentID.id.id, new TypeGroupBehaviour());

        // check if type has properties
        if(typeMainObject.schema.definitions?.root?.properties == null) {
            return;
        }

        // sore previous nodes values
        let nodeID: {id:Node, bbox: {x,y}} = {id:null, bbox:{x:parentID.bbox.x,y:parentID.bbox.y}};
        let counter = 0;
        for (let typeElement in typeMainObject.schema.definitions?.root?.properties) {  
            if (counter>3) return;
            counter++;
            let typeProps = typeMainObject.schema.definitions?.root?.properties[typeElement];
            if(typeProps["type"]=="object") {
                if(typeProps["referenceType"]=="ont-taxonomy") {
                    nodeID = this.addNodeToGraph({id: this.getTaxonomyHref(typeProps["referenceKey"]["namespaceId"],typeProps["referenceKey"]["taxonomyId"])+"childItem", title: this.taxonomyItems.find(f => f.namespaceId == typeProps["referenceKey"]["namespaceId"] && f.taxonomyId == typeProps["referenceKey"]["taxonomyId"])?.name, type: "taxonomy-link-item", x:nodeID.bbox.x,y:nodeID.bbox.y, typedescription:"Taxonomy-Ref"},true);
                    this.nodes.find(p=>p.id==parentID.id).addChild(this.taxonomyItems.find(f => f.namespaceId == typeProps["referenceKey"]["namespaceId"] && f.taxonomyId == typeProps["referenceKey"]["taxonomyId"])?.name,nodeID.id)
                    
                } else if(typeProps["referenceType"]=="ont-type") {
                    let typeHref = this.getTypeHref(typeProps["referenceKey"]["namespaceId"],typeProps["referenceKey"]["typeId"])
                    nodeID = this.addNodeToGraph({id: typeHref+"childItem", title: this.typeItems.find(f => f.self.href == typeHref)?.name, type: "type-link-item", x:nodeID.bbox.x,y:nodeID.bbox.y, typedescription:"Type-Ref"},true);
                    this.nodes.find(p=>p.id==parentID.id).addChild(this.typeItems.find(f => f.self.href == typeHref)?.name,nodeID.id)
                    
                } else {
                    console.warn("Undefined Object found: " , typeProps["referenceType"])
                    nodeID = this.addNodeToGraph({id: parentID.id+typeElement, title: typeElement, type: typeProps["referenceType"], x:nodeID.bbox.x,y:nodeID.bbox.y},true);
                    this.nodes.find(p=>p.id==parentID.id).addChild(typeProps["type"] + " " + typeElement,nodeID.id)
                }
            } else if(typeProps["enum"] ) {
                nodeID = this.addNodeToGraph({id: parentID.id+typeElement, title: typeElement, type: "taxonomy-item", x:nodeID.bbox.x,y:nodeID.bbox.y, typedescription:"enum"},true);
                this.nodes.find(p=>p.id==parentID.id).addChild(typeElement,nodeID.id)
            } else {
                if(typeProps["type"] == "string" || 
                    typeProps["type"] == "integer" || 
                    typeProps["type"] == "boolean" || 
                    typeProps["type"] == "number" ){
                    nodeID = this.addNodeToGraph({id: parentID.id+typeElement, title: typeElement, type: "taxonomy-item", x:nodeID.bbox.x,y:nodeID.bbox.y, typedescription:typeProps["type"]},true);
                    this.nodes.find(p=>p.id==parentID.id).addChild(typeElement,nodeID.id)
                }   
                else {
                    console.warn("Unknown type property found: ", typeElement, typeProps)
                    nodeID = this.addNodeToGraph({id: parentID.id+typeElement, title: typeElement, type: typeProps["type"], x:nodeID.bbox.x,y:nodeID.bbox.y},true);
                    this.nodes.find(p=>p.id==parentID.id).addChild(typeProps["type"],nodeID.id)
                }
            }
            if(nodeID.id != null) {
                this.missingParentConnection.push({parent: parentID.id.id, child:nodeID.id.id,joinTree:true})
            }
        } 
        return {id: parentID.id, bbox: this.getLeftBottomPointOfItem(parentID.id)};
    }

    private addTaxonomyItem(taxonomyMainObject: TaxonomyObject, parentPosition: {x,y}):{id:Node, bbox: {x,y}} {
        parentPosition.x = parentPosition.x+boundingBoxBorder;
        parentPosition.y = parentPosition.y+boundingBoxBorder;
        let groupManager = this.graph.groupingManager;
        let firstItem = true;
        let parentID: {id:Node, bbox: {x,y}};


        parentID = this.addNodeToGraph({id: taxonomyMainObject.href+taxonomyGroupIdMarker, title: taxonomyMainObject.name, dynamicTemplate:"taxonomy-group-node-template",...parentPosition},true);
        taxonomyMainObject.nodeId = parentID.id.id;
        this.nodes.push(new ListNodeModel(this.graph,parentID.id,taxonomyMainObject.name,true,null))

        if(parentID != null) 
        {
            groupManager.markAsTreeRoot(parentID.id.id);
            groupManager.setGroupBehaviourOf(parentID.id.id, new TaxonomyGroupBehaviour());
            firstItem = false;
        }

        //this.addItemsToTaxonomy(taxonomyMainObject, parentID)
        
        return {id: parentID.id, bbox: this.getLeftBottomPointOfItem(parentID.id)};
    }

    private addItemsToTaxonomy(taxonomyMainObject: TaxonomyObject, parentID: {id:Node, bbox: {x,y}}) {
        if(taxonomyMainObject==null){
            throw new Error("No taxonomy parent item available");
        }
        // needed to change between upper and lower new taxonomy item
        let taxonomyItemSize = this.getSizeOfStaticTemplateNode('taxonomy-item');

        let childElements: Array<{href:string,id:Node}> = []
        taxonomyMainObject.itemsData.forEach(childElement => {
            let nodeID = this.addNodeToGraph({id: childElement.self.href, title: childElement.name, type: 'taxonomy-item', x:parentID.bbox.x+(Math.floor(childElements.length/2))*(Number(taxonomyItemSize.width)+10),y:parentID.bbox.y+(childElements.length%2)*(Number(taxonomyItemSize.height)+10)},true);
            childElements.push({href:childElement.self.href,id:nodeID.id});
            this.nodes.find(p=>p.id==parentID.id).addChild(childElement.name,nodeID.id)
            if(nodeID != null) 
            {
                this.missingParentConnection.push({parent: parentID.id.id, child:nodeID.id.id,joinTree:false})
            }
        });

        // add links to the taxonomy
        taxonomyMainObject.itemsData.forEach(parentElement => {
            parentElement.children.forEach(childElement => {
                this.api.getByApiLink<TaxonomyItemRelationApiObject>(childElement, true).then(apiResponse => {
                    let source = childElements.find(e => e.href == apiResponse.data.sourceItem.href);
                    let target = childElements.find(e => e.href == apiResponse.data.targetItem.href);
                    this.addEdgeToTaxonomy(source.id.id,target.id.id);
                });
            });
        })
    }

    /**
     * add a new node to both graphs, if the node isn't already there
     * @param source source node
     * @param target target node
     */
    private addEdgeToTaxonomy(source: string|number, target: string|number) {
        let path = {source: source, target: target,markerEnd : {
            template: "arrow",
            scale: 0.8,
            relativeRotation: 0,
        }}
        this.graph.addEdge(path,false)
    }

    /**
     * add a new node to both graphs, if the node isn't already there
     * @param node, node to add to the graph
     * @returns id of the new added node and the left bottom point of the node
     */
    private addNodeToGraph(node: Node, redrawGraph: boolean): {id:Node, bbox: {x:number,y:number}} {
        node.id = String(node.id).replace(RegExp(/\/\/|\/|:| /g),"")
        // add some random number (unix time stamp) to the id, no make it unique
        let nodeIdOrig = node.id;
        node.id = nodeIdOrig + "-" + Math.floor(Date.now())

        while(this.graph.nodeList.some(element => element.id == node.id)){
            node.id = nodeIdOrig + "-" + Math.floor(Date.now())
        }

        node.y = node.y + 10;

        // if the node template based on a static template, change x and y coordinate to the center of the node
        if(node.type) {
            let {width, height} = this.getSizeOfStaticTemplateNode(node.type);
            node.x = node.x+width/2;
            node.y = node.y+height/2;
        }
        
        //this.graph?.addNode(node,redrawGraph);
        //this.graphoverview?.addNode(node,redrawGraph);
        this.graph?.addNode(node,false);
        this.graphoverview?.addNode(node,false);

        this.totalNodesAdded++;
        this.isLoading = (this.totalNodesAdded/this.totalNodesToAdd)*100;
        
        return {id: node, bbox: this.getLeftBottomPointOfItem(node)};
    }

    /**
     * get the size of a static template for further calculation
     * @param nodeType, name of the static template
     * @returns size of the node
     */
    private getSizeOfStaticTemplateNode(nodeType: string): {width:number, height:number} {
        let width = this.graph.staticTemplateRegistry.getNodeTemplate(nodeType)._groups[0][0].getElementsByTagName("rect")[0].getAttribute("width");
        let height = this.graph.staticTemplateRegistry.getNodeTemplate(nodeType)._groups[0][0].getElementsByTagName("rect")[0].getAttribute("height");
        return {width,height}
    }

    /**
     * get left bottom point of new added node, for correct positioning of the next node
     * @param nodeID, id of the node as string or number
     * @returns left bottom point of the node {x,y}
     */
    private getLeftBottomPointOfItem(node: Node): {x,y} {
        
        if (node.type) {
            let {width, height} = this.getSizeOfStaticTemplateNode(node.type);
            return {x:node.x-width/2,y:node.y+height/2}
        } else {
            // TODO: fix
            return {x:node.x,y:node.y}
        }
        /*const bbox = this.graph.getNodeBBox(node.id);
        const boxes: Rect[] = [];
        boxes.push({
            x: bbox.x+node.x,
            y: bbox.y+node.y,
            width: bbox.width,
            height: bbox.height,
        });
        let tempRect = calculateBoundingRect(...boxes);

        return {x:tempRect.x,y:tempRect.y+tempRect.height}*/
    }

    private onNodeClick(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node, key: string }>) {
        
        if (event.detail.eventSource !== "USER_INTERACTION") {
            return;
        }
        event.preventDefault();
        const node = event.detail.node;
        console.log("Click event", event)
        
        if(node.dynamicTemplate==="taxonomy-group-node-template" && event.detail.key == "expandNode") {
            if(this.graph.groupingManager.getAllChildrenOf(node.id).size>0) {
                this.graph.groupingManager.getAllChildrenOf(node.id).forEach(child => {
                    this.graph.groupingManager.removeNodeFromGroup(node.id,child)
                    this.graph.removeNode(child,true);
                    this.graphoverview.removeNode(child,true);
                })
            } 
            else {
                this.addItemsToTaxonomy(this.taxonomyItems.find(t => t.nodeId == node.id), {id: node, bbox: this.getLeftBottomPointOfItem(node)})
                this.graph.completeRender();
                this.addChildnodesToParents();
            }
        }

        if(event.detail.key == "header") {
            this.selectedNode = node;
        }
        
        if (node.type !== "taxonomy-item") {
            return;
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
        this.graphoverview.removeNode(42424242424242424242424242424242421,false);
        this.graphoverview.addNode({id:42424242424242424242424242424242421,class:"invisible-rect", dynamicTemplate:'overview-node-template',x:currentView.x,y:currentView.y,width:currentView.width,height:currentView.height},false);
    }

    private onZoomChange(event: CustomEvent<{ eventSource: "API" | "USER_INTERACTION" | "INTERNAL", node: Node }>) {
        this.renderMainViewPositionInOverviewGraph();
    }

    private checkGraphRender() {
        this.graph.nodeList = []
        const start = Date.now();
        console.log("start drawing", start)
        let items = 80;
        for (let iy = 0; iy < items; iy++) {
            for (let ix = 0; ix < items; ix++) {
                //console.log(ix,iy)
                this.graph.addNode({x:ix*120,y:iy*60,id:Date.now(),type:'taxonomy-item'},true)    
            }
        }
        //this.graph.completeRender();
        const end = Date.now();
        console.log("end drawing", end)
        console.log("duration ", end-start)
        console.log("items ", this.graph.nodeList.length)
    }

    private renderMainViewPositionInOverviewGraph() {
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
        if(direction=='down') {
            currentView.y = currentView.y-dirY;
        } else if(direction=='right') {
            currentView.x = currentView.x-dirX;
        } else if(direction=='left') {
            currentView.x = currentView.x+dirX;
        } else if(direction=='up') {
            currentView.y = currentView.y+dirY;
        } 
        currentView.x = currentView.x-div;
        currentView.y = currentView.y-div;
        currentView.height = currentView.height+2*div;
        currentView.width = currentView.width+2*div;

        /*this.graph.nodeList.forEach(node => {            
            this.graph.moveNode(node.id, node.x+dirX, node.y+dirY, false);
        })*/


        this.graph.zoomToBox(currentView);

        this.graph.completeRender();
    }
}