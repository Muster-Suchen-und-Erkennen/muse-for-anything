import GraphEditor from "@ustutt/grapheditor-webcomponent/lib/grapheditor";
import { Node } from "@ustutt/grapheditor-webcomponent/lib/node";
import { observable } from "aurelia-framework";
import { ApiLink, ApiObject, ApiResponse, PageApiObject } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";
import { NormalizedApiSchema } from "rest/schema-objects";
import { SchemaService } from "rest/schema-service";
import { TaxonomyApiObject, TaxonomyItemApiObject, TaxonomyItemRelationApiObject } from "../taxonomy-graph";

export const smallMarkerSize: number = 0.8;
export const largeMarkerSize: number = 1.8;


export interface TypeApiObject extends ApiObject {
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
                properties: any | null,
                propertyOrder: {
                    [prop: string]: number,
                },
                enum: any,
                const: any,
                titel: string | null,
                type: [string]

            } | null
        },
        description: string | null;
        titel: string;
    };
}

export enum DataItemTypeEnum {
    TaxonomyItem = "taxonomyItem",
    TaxonomyItemProperty = "taxonomyItemProperty",
    TaxonomyProperty = "taxonomy",
    TypeItem = "typeItem",
    TypeProperty = "type",
    ObjectProperty = "object",
    ArrayProperty = "array",
    StringProperty = "string",
    NumberProperty = "number",
    IntegerProperty = "integer",
    EnumProperty = "enum",
    BooleanProperty = "boolean",
    EllipsisProperty = "ellipsis",
    Undefined = "undefined",
}

export const GROUP_DATA_ITEM_TYPE_SET = new Set([
    DataItemTypeEnum.TypeItem,
    DataItemTypeEnum.TaxonomyItem,
]);

export const CHILD_ITEM_TYPE_SET = new Set([
    DataItemTypeEnum.TaxonomyProperty,
    DataItemTypeEnum.TypeProperty,
    DataItemTypeEnum.StringProperty,
    DataItemTypeEnum.NumberProperty,
    DataItemTypeEnum.IntegerProperty,
    DataItemTypeEnum.EnumProperty,
    DataItemTypeEnum.BooleanProperty,
    DataItemTypeEnum.TaxonomyItemProperty,
]);

export const TYPE_DATA_ITEM_TYPE_SET = new Set([
    DataItemTypeEnum.TypeItem,
    DataItemTypeEnum.ObjectProperty,
    DataItemTypeEnum.ArrayProperty,
    DataItemTypeEnum.EllipsisProperty,
    DataItemTypeEnum.TaxonomyProperty,
    DataItemTypeEnum.TypeProperty,
    DataItemTypeEnum.StringProperty,
    DataItemTypeEnum.NumberProperty,
    DataItemTypeEnum.IntegerProperty,
    DataItemTypeEnum.EnumProperty,
    DataItemTypeEnum.BooleanProperty,
]);

export const TAXONOMY_DATA_ITEM_TYPE_SET = new Set([
    DataItemTypeEnum.TaxonomyItem,
    DataItemTypeEnum.TaxonomyItemProperty,
]);


export class DataItemModel {
    public id: string;
    public name: string;
    public href: string;
    public description: string;
    public sortKey: number | null;
    public itemType: DataItemTypeEnum;
    public node: Node | null;

    public icon: string;
    public rootId: string | null;
    public parentIds: Set<string>;
    public referenceTargetId: string | null;
    public children: DataItemModel[];
    public expanded: boolean;
    public visible: boolean;
    public abstract: boolean;
    @observable() childrenLoaded: boolean = false;
    @observable() isSelected: boolean;
    @observable() isVisibleInGraph: boolean;
    @observable() isSearchResult: boolean;
    @observable() childIsInResult: boolean;
    @observable() positionIsFixed: boolean;
    private graph: GraphEditor;


    constructor(graph: GraphEditor, id: string, name: string, abstract: boolean, href: string, description: string, itemType: DataItemTypeEnum, sortKey: number | null = null, isVisible = true, referenceTargetId: string | null = null) {
        this.id = id;
        this.rootId = null;
        this.parentIds = new Set();
        this.referenceTargetId = referenceTargetId;
        this.node = null;
        this.name = name;
        this.sortKey = sortKey;
        this.abstract = abstract;
        this.href = href;
        this.description = description;
        this.itemType = itemType;
        this.expanded = false;
        this.visible = isVisible;
        this.graph = graph;
        this.children = [];
        this.isVisibleInGraph = true;
        this.positionIsFixed = false;
        this.childIsInResult = false;
    }

    hasChildren(): boolean {
        if (this.itemType === DataItemTypeEnum.TypeItem || this.itemType === DataItemTypeEnum.TaxonomyItem) {
            return true;
        }
        if (this.children.length > 0) {
            return true;
        }
        return false;
    }

    toggleNode(): void {
        for (let i = 0; i < this.children.length; i++) {
            this.children[i].visible = !this.children[i].visible;
            if (this.expanded) {
                this.children[i].toggleNode();
            }
        }
        this.expanded = !this.expanded;
        if (this.expanded) {
            this.icon = "arrow-down";
        } else {
            this.icon = "arrow-right";
        }
    }

    togglePositionFixed(): void {
        this.positionIsFixed = !this.positionIsFixed;
        if (this.positionIsFixed) {
            this.node.fx = this.node.x;
            this.node.fy = this.node.y;
        } else {
            delete this.node.fx;
            delete this.node.fy;
        }
    }

    isSelectedChanged(newValue: boolean): void {
        if (newValue) {
            this.graph.selectNode(this.id);
        } else {
            this.graph.deselectNode(this.id);
        }
        this.graph.updateHighlights();

    }

    addChild(id: string, name: string, abstract: boolean, href: string, description: string, itemType: DataItemTypeEnum, sortKey: number | null = null, referenceTargetId: string | null = null): DataItemModel {
        const childItem = new DataItemModel(this.graph, id, name, abstract, href, description, itemType, sortKey, false, referenceTargetId);
        childItem.rootId = this.rootId ?? this.id;
        childItem.parentIds.add(this.id);
        this.children.push(childItem);
        this.icon = "arrow-right";
        this.expanded = false;
        return childItem;
    }

    addChildItem(item: DataItemModel): void {
        item.rootId = this.rootId ?? this.id;
        item.parentIds.add(this.id);
        this.children.push(item);
        this.icon = "arrow-right";
        this.expanded = false;
    }

    getLink(): string {
        if (this.itemType === DataItemTypeEnum.TypeItem) {
            const namespaceID = this.href.split("namespaces/")[1].split("/")[0];
            const typeID = this.href.split("types/")[1].split("/")[0];

            return `http://localhost:5000/explore/ont-namespace/:${namespaceID}/ont-type/:${typeID}`;
        } else if (this.itemType === DataItemTypeEnum.TaxonomyItem) {
            const namespaceID = this.href.split("namespaces/")[1].split("/")[0];
            const typeID = this.href.split("taxonomies/")[1].split("/")[0];

            return `http://localhost:5000/explore/ont-namespace/:${namespaceID}/ont-taxonomy/:${typeID}`;
        }
    }
}


// eslint-disable-next-line complexity
export function mapDataItemToGraphNode(item: DataItemModel): Node | null {
    if (item.node != null) {
        return item.node;
    }

    if (item.itemType === DataItemTypeEnum.TypeItem) {
        return {
            id: item.id,
            x: 0,
            y: 0,
            type: "type-node",
            dynamicTemplate: "type-group-node-template",
            title: item.name,
            description: item.description,
            abstract: item.abstract,
            isGroupNode: true,
        };
    }
    if (item.itemType === DataItemTypeEnum.TaxonomyItem) {
        return {
            id: item.id,
            x: 0,
            y: 0,
            type: "taxonomy-node",
            dynamicTemplate: "taxonomy-group-node-template",
            title: item.name,
            description: item.description,
            isGroupNode: true,
        };
    }

    if (item.itemType === DataItemTypeEnum.TaxonomyProperty) {
        return {
            id: item.id,
            x: 0,
            y: 0,
            type: "taxonomy-link-item",
            title: item.name,
            typedescription: "Taxonomy-Ref",
            typedescriptionHref: `#${item.itemType}`,
            isGroupNode: false,
        };
    }
    if (item.itemType === DataItemTypeEnum.TypeProperty) {
        return {
            id: item.id,
            x: 0,
            y: 0,
            type: "type-link-item",
            title: item.name,
            typedescription: "Type-Ref",
            typedescriptionHref: `#${item.itemType}`,
            isGroupNode: false,
        };
    }
    if (item.itemType === DataItemTypeEnum.EnumProperty ||
        item.itemType === DataItemTypeEnum.BooleanProperty ||
        item.itemType === DataItemTypeEnum.IntegerProperty ||
        item.itemType === DataItemTypeEnum.NumberProperty ||
        item.itemType === DataItemTypeEnum.StringProperty ||
        item.itemType === DataItemTypeEnum.ObjectProperty ||
        item.itemType === DataItemTypeEnum.ArrayProperty ||
        item.itemType === DataItemTypeEnum.EllipsisProperty ||
        item.itemType === DataItemTypeEnum.Undefined) {
        return {
            id: item.id,
            x: 0,
            y: 0,
            type: "type-item",
            title: item.name,
            typedescription: item.itemType,
            typedescriptionHref: `#${item.itemType}`,
            isGroupNode: false,
        };
    }
    if (item.itemType === DataItemTypeEnum.TaxonomyItemProperty) {
        return {
            id: item.id,
            x: 0,
            y: 0,
            type: "taxonomy-item",
            title: item.name,
            isGroupNode: false,
        };
    }
    return null;
}


/**
 * get the corresponding DataItemTypeEnum from the api response for a given element to store the correct value in the datamodel
 * @param type type from the api response
 * @returns the corresponding DataItemTypeEnum
 */
// eslint-disable-next-line complexity
function mapTypeEnums(type: { type: Set<string>, referenceType?: string, enum?: unknown[], const?: unknown }): DataItemTypeEnum {
    if (type.enum != null || type.const !== undefined) {
        return DataItemTypeEnum.EnumProperty;
    }
    if (type.type == null) {
        return DataItemTypeEnum.Undefined;
    }
    if (type.type.has("object")) {
        if (type.referenceType === "ont-taxonomy") {
            return DataItemTypeEnum.TaxonomyProperty;
        }
        if (type.referenceType === "ont-type") {
            return DataItemTypeEnum.TypeProperty;
        }
        return DataItemTypeEnum.ObjectProperty;
    }
    if (type.type.has("array")) {
        return DataItemTypeEnum.ArrayProperty;
    }
    if (type.type.has("string")) {
        return DataItemTypeEnum.StringProperty;
    }
    if (type.type.has("integer")) {
        return DataItemTypeEnum.IntegerProperty;
    }
    if (type.type.has("boolean")) {
        return DataItemTypeEnum.BooleanProperty;
    }
    if (type.type.has("number")) {
        return DataItemTypeEnum.NumberProperty;
    }
    return DataItemTypeEnum.Undefined;
}


/**
 * load all type items of the namespace
 * @param rootLink root link from the navigation-service
 * @param ignoreCache
 */
export async function loadTypes(api: BaseApiService, rootLink: ApiLink, ignoreCache: boolean, isFirstPage = true): Promise<{ totalTypes: number, typeApiResponses: Array<Promise<ApiResponse<TypeApiObject>>> }> {
    const apiResponse = await api.getByApiLink<PageApiObject>(rootLink, ignoreCache || isFirstPage);
    // load each type of the namespace
    const typeApiResponses = apiResponse.data.items?.map(element => {
        return api.getByApiLink<TypeApiObject>(element, ignoreCache);
    });

    const extraPages = await Promise.all(apiResponse.links.filter(link => link.rel.includes("next")).map(link => {
        return loadTypes(api, link, ignoreCache, false).then(result => result.typeApiResponses);
    }));

    return {
        totalTypes: apiResponse.data.collectionSize,
        typeApiResponses: typeApiResponses.concat(...extraPages),
    };
}

export function resourceLinkToNodeId(link: ApiLink): string {
    const resourceKey = Object.keys(link.resourceKey)
        .map(keyVar => `${keyVar}_${link.resourceKey[keyVar]}`)
        .join("__");
    return `${link.resourceType}__${resourceKey}`;
}

export function typeApiResponseToDataItemModel(apiResponse: ApiResponse<TypeApiObject>, graph: GraphEditor): DataItemModel {
    const data = apiResponse.data;
    const nodeID = resourceLinkToNodeId(data.self);
    return new DataItemModel(graph, nodeID, data.name, data.abstract, data.self.href, data.schema.description, DataItemTypeEnum.TypeItem, null);
}

export async function addTypeChildrenToDataItem(apiResponse: ApiResponse<TypeApiObject>, dataItem: DataItemModel, api: BaseApiService, apiSchemas: SchemaService) {
    const objectCreate = apiResponse.links.find(link => link.resourceType === "ont-object" && link.rel.some(rel => rel === "create"));

    const schema = await apiSchemas.getSchema(objectCreate.schema).then((schema) => schema.getNormalizedApiSchema());

    // eslint-disable-next-line complexity
    const visitor = async (schema: NormalizedApiSchema, parentSchemas: NormalizedApiSchema[], key: string, path: string, sortKey, parent: DataItemModel, root: DataItemModel) => {
        if (parentSchemas.includes(schema) || parentSchemas.length > 15) {
            parent.addChild(`${root.id}___${path}---ellipsis`, "...", false, root.href, "recursion / nesting too deep", DataItemTypeEnum.EllipsisProperty, 0);
            return; // detected cycle! or nesting too deep
        }
        const normalized = schema.normalized;
        const typeEnum: DataItemTypeEnum = mapTypeEnums(normalized);

        let href = apiResponse.data.self.href;
        let referenceTarget: string | null = null;

        const isReference = normalized.referenceKey != null && normalized.referenceType != null;
        if (isReference) {
            const links = await api.resolveLinkKey(normalized.referenceKey, normalized.referenceType);
            links.forEach(link => {
                if (!link.rel.some(rel => rel === "collection")) {
                    referenceTarget = resourceLinkToNodeId(link);
                    href = link.href;
                }
            });
        }
        const childId = `${root.id}___${path}--${key}`;
        const childItem = parent.addChild(childId, normalized.title ?? key, false, href, normalized.description ?? "", typeEnum, sortKey, referenceTarget);

        const newPath = (path ? `${path}--` : "") + key;

        const nested: Array<Promise<unknown>> = [];

        if (normalized.mainType === "object" && !isReference) {
            schema.getPropertyList().forEach((prop) => {
                nested.push(visitor(prop.propertySchema, [...parentSchemas, schema], prop.propertyName, newPath, prop.sortKey, childItem, root));
            });
        }
        if (normalized.mainType === "array") {
            schema.getItemList(1).forEach((prop) => {
                nested.push(visitor(prop.itemSchema, [...parentSchemas, schema], prop.itemIndex.toString(), newPath, prop.itemIndex, childItem, root));
            });
        }

        await Promise.all(nested);
    };

    const nested: Array<Promise<unknown>> = [];

    schema.getPropertyList().forEach((prop) => {
        nested.push(visitor(prop.propertySchema, [], prop.propertyName, "", prop.sortKey, dataItem, dataItem));
    });

    await Promise.all(nested);
}







/**
 * load all taxonomy items of the namespace
 * @param rootLink root link from the navigation-service
 * @param ignoreCache
 */
export async function loadTaxonomies(api: BaseApiService, rootLink: ApiLink, ignoreCache: boolean, isFirstPage = true): Promise<{ totalTaxonomies: number, taxonomyApiResponses: Array<Promise<ApiResponse<TaxonomyApiObject>>> }> {
    const apiResponse = await api.getByApiLink<PageApiObject>(rootLink, ignoreCache || isFirstPage);
    // load each type of the namespace
    const typeApiResponses = apiResponse.data.items?.map(element => {
        // always load taxonomy resources fresh from source to get embedded taxonomy items and item-relations into the cache
        return api.getByApiLink<TaxonomyApiObject>(element, "ignore-embedded"); // FIXME find a better workaround for efficient cache handling here
    });

    const extraPages = await Promise.all(apiResponse.links.filter(link => link.rel.includes("next")).map(link => {
        return loadTaxonomies(api, link, ignoreCache, false).then(result => result.taxonomyApiResponses);
    }));

    return {
        totalTaxonomies: apiResponse.data.collectionSize,
        taxonomyApiResponses: typeApiResponses.concat(...extraPages),
    };
}

export function taxonomyApiResponseToDataItemModel(apiResponse: ApiResponse<TaxonomyApiObject>, graph: GraphEditor): DataItemModel {
    const data = apiResponse.data;
    const nodeID = resourceLinkToNodeId(data.self);
    return new DataItemModel(graph, nodeID, data.name, false, data.self.href, data.description, DataItemTypeEnum.TaxonomyItem, null);
}


function taxonomyItemToDataItem(taxonomyItem: TaxonomyItemApiObject, graph: GraphEditor): DataItemModel {
    return new DataItemModel(graph, resourceLinkToNodeId(taxonomyItem.self), taxonomyItem.name, false, taxonomyItem.self.href, taxonomyItem.description, DataItemTypeEnum.TaxonomyItemProperty, taxonomyItem.sortKey, false);
}

export async function addTaxonomyChildrenToDataItem(apiResponse: ApiResponse<TaxonomyApiObject>, dataItem: DataItemModel, graph: GraphEditor, api: BaseApiService) {
    const taxonomyItems = new Map<string, TaxonomyItemApiObject>();
    const taxonomyItemRelations = new Map<string, Set<string>>();
    await Promise.all(apiResponse.data.items.map(element => {
        return api.getByApiLink<TaxonomyItemApiObject>(element)
            .then(apiResponse => {
                const taxonomyItem = apiResponse.data;
                taxonomyItems.set(taxonomyItem.self.href, taxonomyItem);
                return Promise.all(taxonomyItem.children.map(childRelationLink => {
                    return api.getByApiLink<TaxonomyItemRelationApiObject>(childRelationLink);
                }));
            })
            .then(childRelationsResponses => {
                childRelationsResponses.forEach(relation => {
                    const source = relation.data.sourceItem.href;
                    const target = relation.data.targetItem.href;
                    if (taxonomyItemRelations.has(source)) {
                        taxonomyItemRelations.get(source).add(target);
                    } else {
                        taxonomyItemRelations.set(source, new Set<string>([target]));
                    }
                });
            });
    }));

    function addTaxonomyItemsRecursive(parentItemModel: DataItemModel, taxonomyItem: TaxonomyItemApiObject) {
        const itemModel = taxonomyItemToDataItem(taxonomyItem, graph);
        parentItemModel.addChildItem(itemModel);
        const children = taxonomyItemRelations.get(taxonomyItem.self.href);
        if (children != null) {
            children.forEach(child => {
                const childItem = taxonomyItems.get(child);
                if (childItem == null) {
                    console.log("Bad taxonomy child!", child, children, taxonomyItem);
                    return;
                }
                addTaxonomyItemsRecursive(itemModel, childItem);
            });
        }
    }


    taxonomyItems.forEach(taxonomyItem => {
        if (taxonomyItem.isToplevelItem) {
            addTaxonomyItemsRecursive(dataItem, taxonomyItem);
        }
    });
}

/**
 * A comparator to sort data item models by sort key first, then alphabetical by name.
 *
 * @param a first data item model
 * @param b second data item model
 * @returns the comparison result
 */
export function compareDataItems(a: DataItemModel, b: DataItemModel): number {
    const aKey = a.sortKey;
    const bKey = b.sortKey;
    if (aKey != null && bKey != null) {
        const delta = aKey - bKey;
        if (delta !== 0) {
            return delta;
        }
    }
    if (aKey != null && bKey == null) {
        return -1; // null sort keys are sorted last
    }
    if (aKey == null && bKey != null) {
        return 1; // null sort keys are sorted last
    }

    const aName = a.name.toUpperCase();
    const bName = b.name.toUpperCase();

    if (aName < bName) {
        return -1;
    }
    if (aName > bName) {
        return 1;
    }
    return 0;
}
