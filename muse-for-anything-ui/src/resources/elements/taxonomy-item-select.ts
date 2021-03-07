import { bindable, bindingMode, child, autoinject, observable } from "aurelia-framework";
import { nanoid } from "nanoid";
import { ApiLinkKey, ApiResponse } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";
import { TaxonomyApiObject, TaxonomyItemApiObject, TaxonomyItemRelationApiObject } from "resources/elements/taxonomy-graph";

interface ItemChoice {
    index: number;
    item: TaxonomyItemApiObject;
    parents: Set<number>;
    children: Set<number>;
    level: number;
}

function taxonomyItemComparator(a: TaxonomyItemApiObject, b: TaxonomyItemApiObject) {
    const sortKey = (a?.sortKey ?? 0) - (b?.sortKey ?? 0);
    if (sortKey < 0) { // sort key trumps everything
        return -1;
    }
    if (sortKey > 0) {
        return 1;
    }
    if (a.name < b.name) { // sort by name when same sortKey
        return -1;
    }
    if (a.name > b.name) {
        return 1;
    }
    if (a.self.href < b.self.href) { // sort by id when same name and sortKey
        return -1;
    }
    if (a.self.href > b.self.href) {
        return 1;
    }
    return 0;
}

@autoinject
export class TaxonomyItemSelect {
    @bindable label: string;
    @bindable taxonomyKey: ApiLinkKey;
    @bindable({ defaultBindingMode: bindingMode.twoWay }) value: ApiLinkKey;

    slug = nanoid(8);

    @observable() taxonomy: TaxonomyApiObject;

    items: TaxonomyItemApiObject[];

    datalistVisible: boolean = false;
    datalistChoices: ItemChoice[];

    cursor: number = 0;
    selectedItems: Set<number> = new Set();

    showTreeControls: boolean = false;

    @observable() closedGroups: Set<number> = new Set();
    hiddenItems: Set<number> = new Set();
    filteredItems: Set<number> = new Set();

    @observable() filter: string;

    //@child(".input-valid-check") formInput: Element;

    private apiService: BaseApiService;

    constructor(apiService: BaseApiService) {
        this.apiService = apiService;
    }

    taxonomyKeyChanged(newValue: ApiLinkKey) {
        if (newValue == null) {
            return;
        }
        this.apiService.resolveLinkKey(newValue, "ont-taxonomy")
            .then(links => links.find(link => !link.rel.some(rel => rel === "collection")))
            .then(taxonomyLink => {
                if (taxonomyLink == null) {
                    // TODO no tax found
                    return;
                }
                return this.apiService.getByApiLink<TaxonomyApiObject>(taxonomyLink);
            })
            .then(result => {
                this.taxonomy = result.data;
            });
    }

    taxonomyChanged(newValue: TaxonomyApiObject) {
        const itemPromises = [];
        const relationPromises = [];
        const items: TaxonomyItemApiObject[] = [];
        const relations: TaxonomyItemRelationApiObject[] = [];
        newValue.items.forEach(itemLink => {
            itemPromises.push(this.apiService.getByApiLink<TaxonomyItemApiObject>(itemLink, false).then(apiResponse => {
                items.push(apiResponse.data);
                apiResponse.data.children.forEach(childRelationLink => {
                    relationPromises.push(this.apiService.getByApiLink<TaxonomyItemRelationApiObject>(childRelationLink, false).then(relationApiResponse => {
                        relations.push(relationApiResponse.data);
                    }));
                });
            }));
        });
        Promise.all(itemPromises)
            .then(() => Promise.all(relationPromises))
            .then(() => {
                const relationMap: Map<string, Set<string>> = new Map();
                relations.forEach(relation => {
                    const source = relation.sourceItem.href;
                    const target = relation.targetItem.href;
                    if (!relationMap.has(source)) {
                        relationMap.set(source, new Set());
                    }
                    relationMap.get(source).add(target);
                });
                const itemMap: Map<string, TaxonomyItemApiObject> = new Map();
                this.updateTaxonomyChoices(items, relationMap);
            });
    }

    updateTaxonomyChoices(items: TaxonomyItemApiObject[], relationMap: Map<string, Set<string>>) {
        const itemMap: Map<string, TaxonomyItemApiObject> = new Map();
        const topLevelItems: TaxonomyItemApiObject[] = [];
        items.forEach(item => {
            itemMap.set(item.self.href, item);
            if (item.isToplevelItem) {
                topLevelItems.push(item);
            }
        });

        let isTree = false;
        const choices: ItemChoice[] = [];
        topLevelItems.sort(taxonomyItemComparator);

        const recursiveItemsAdd = (item: TaxonomyItemApiObject, currentItemLevel: number = 0, parents: Set<number> = null): Set<number> => {
            if (currentItemLevel > 0) {
                isTree = true;
            }
            const childChoices: Set<number> = new Set();

            const parentChoices: Set<number> = new Set(parents ?? []);

            const itemChoice: ItemChoice = {
                index: 0,
                item: item,
                parents: parentChoices,
                children: childChoices,
                level: currentItemLevel,
            };
            const index = choices.push(itemChoice) - 1;
            itemChoice.index = index;
            childChoices.add(index);
            const newParents = new Set(parentChoices);
            newParents.add(index);

            const childItems: TaxonomyItemApiObject[] = [];
            relationMap.get(item.self.href)?.forEach(childId => {
                if (itemMap.has(childId)) {
                    childItems.push(itemMap.get(childId));
                }
            });
            childItems.sort(taxonomyItemComparator);
            childItems.forEach(item => {
                recursiveItemsAdd(item, currentItemLevel + 1, newParents).forEach(childChoice => childChoices.add(childChoice));
            });

            return childChoices;
        };
        topLevelItems.forEach(item => {
            recursiveItemsAdd(item);
        });

        this.items = items;
        this.datalistChoices = choices;
        this.showTreeControls = isTree;
        this.closedGroups = new Set();
        this.hiddenItems = new Set();
        this.filteredItems = new Set();
        this.filterChanged(this.filter);
    }

    filterChanged(newValue: string) {
        if (this.datalistChoices == null || this.datalistChoices.length === 0) {
            return;
        }

        const filter = (newValue ?? "").toLowerCase().trim();
        if (filter === "") {
            if (this.filteredItems?.size !== this.datalistChoices.length) {
                const filteredItems = new Set<number>();
                this.datalistChoices.forEach((choice, choiceId) => filteredItems.add(choiceId));
                this.filteredItems = filteredItems;
            }
            return;
        }
        const filteredItems = new Set<number>();
        this.datalistChoices.forEach((choice, choiceId) => {
            const name = choice.item.name.toLowerCase();
            if (name.includes(filter)) {
                choice.parents.forEach(parentId => filteredItems.add(parentId));
                filteredItems.add(choiceId);
            }
        });
        this.filteredItems = filteredItems;
        if (!filteredItems.has(this.cursor)) {
            this.moveCursorDown();
        }
    }

    closedGroupsChanged(newValue: Set<number>) {
        const hiddenItems: Set<number> = new Set();
        newValue?.forEach(groupId => {
            const choice = this.datalistChoices?.[groupId];
            if (choice == null) {
                return;
            }
            choice.children.forEach(childId => {
                if (childId !== groupId) {
                    hiddenItems.add(childId);
                }
            });
        });
        this.hiddenItems = hiddenItems;
        if (hiddenItems.has(this.cursor)) {
            this.moveCursorDown();
        }
    }

    valueChanged(newValue: ApiLinkKey, oldValue) {
        if (newValue == null) {
            this.selectedItems = new Set();
            return;
        }
        const keys = Object.keys(newValue);
        const selectedItems: Set<number> = new Set();
        this.datalistChoices?.forEach(choice => {
            const choiceKey = choice.item.self.resourceKey;
            if (keys.every(key => choiceKey[key] === newValue[key])) {
                selectedItems.add(choice.index);
            }
        });
        this.selectedItems = selectedItems;
    }

    selectItem(choiceId) {
        const key = this.datalistChoices?.[choiceId]?.item?.self?.resourceKey;
        if (key != null) {
            if (this.value == null || Object.keys(key).some(k => this.value[k] !== key[k])) {
                this.value = key;
            }
        }
    }

    toggleGroup(groupId: number) {
        if (this.filter) {
            return;
        }
        if (!(this.datalistChoices?.[groupId]?.children?.size > 1)) {
            return;
        }
        const closed = new Set(this.closedGroups);
        if (closed.has(groupId)) {
            closed.delete(groupId);
        } else {
            closed.add(groupId);
        }
        this.closedGroups = closed;
    }

    onKeyDown(event: KeyboardEvent) {
        if (event.ctrlKey) {
            if (event.key === "Enter") {
                this.selectItem(this.cursor);
                return false;
            }
        }
        return true;
    }

    onKeyUp(event: KeyboardEvent) {
        if (event.ctrlKey) {
            if (event.key === "ArrowLeft") {
                if (!this.filter && !this.closedGroups.has(this.cursor)) {
                    this.toggleGroup(this.cursor);
                }
            }
            if (event.key === "ArrowRight") {
                if (!this.filter && this.closedGroups.has(this.cursor)) {
                    this.toggleGroup(this.cursor);
                }
            }
        }
        if (event.key === "ArrowDown") {
            this.moveCursorDown();
        }
        if (event.key === "ArrowUp") {
            this.moveCursorUp();
        }

        return true; // do not prevent default action
    }

    moveCursorDown() {
        let searchList: ItemChoice[];
        if (this.filter) {
            searchList = this.datalistChoices.filter(choice => this.filteredItems.has(choice.index));
        } else {
            searchList = this.datalistChoices.filter(choice => !this.hiddenItems.has(choice.index));
        }
        const firstIndex = searchList[0]?.index ?? 0;
        let nextIndex;
        searchList.forEach(element => {
            if (nextIndex != null) {
                return;
            }
            if (element.index > this.cursor) {
                nextIndex = element.index;
            }
        });
        this.cursor = nextIndex ?? firstIndex;
    }

    moveCursorUp() {
        let searchList: ItemChoice[];
        if (this.filter) {
            searchList = this.datalistChoices.filter(choice => this.filteredItems.has(choice.index));
        } else {
            searchList = this.datalistChoices.filter(choice => !this.hiddenItems.has(choice.index));
        }
        let lastIndex = 0;
        let nextIndex;
        searchList.forEach(element => {
            if (element.index < this.cursor) {
                nextIndex = element.index;
            }
            lastIndex = element.index;
        });
        this.cursor = nextIndex ?? lastIndex;
    }

}
