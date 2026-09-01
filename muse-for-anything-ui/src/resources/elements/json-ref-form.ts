import { DialogService } from "aurelia-dialog";
import { autoinject, bindable, bindingMode, observable, TaskQueue } from "aurelia-framework";
import { nanoid } from "nanoid";
import { ApiLink, ApiObject } from "rest/api-objects";
import { BaseApiService } from "rest/base-api";
import { NormalizedApiSchema } from "rest/schema-objects";
import { SchemaService } from "rest/schema-service";
import { ApiObjectChooserDialog } from "./api-object-chooser-dialog";


interface JSONRef {
    $ref: string;
}

interface ReferenceChoice {
    key: string;
    title: string;
}


@autoinject()
export class JsonRefForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable required: boolean = false;
    @bindable context: any;
    @bindable debug: boolean = false;
    @bindable actions: Iterable<string>;
    @bindable actionSignal: unknown;
    @bindable({ defaultBindingMode: bindingMode.toView }) valueIn: JSONRef | null;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valueOut: JSONRef | null;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;

    showInfo: boolean = false;

    slug = nanoid(8);

    description: string = "";

    isNullable: boolean = true;

    // broken out value
    @observable() base: string | null = null;
    @observable() ref: string | null = null;

    refChoices: ReferenceChoice[] = [];

    namespaceApiLink: ApiLink | null = null;
    baseApiLink: ApiLink | null = null;
    baseTypeChoices: ReferenceChoice[] = [];

    private queue: TaskQueue;
    private apiService: BaseApiService;
    private schemas: SchemaService;
    private dialogService: DialogService;

    constructor(queue: TaskQueue, rest: BaseApiService, schemas: SchemaService, dialogservice: DialogService) {
        this.queue = queue;
        this.apiService = rest;
        this.schemas = schemas;
        this.dialogService = dialogservice;
    }

    toggleInfo() {
        this.showInfo = !this.showInfo;
        return false;
    }

    private splitUrl(value: string | null) {
        if (value == null) {
            return { base: null, ref: null };
        }

        const split = value.split("#", 2);
        const base = split[0] ? split[0] : null;

        if (split.length === 1) {
            return { base: base, ref: null };
        }
        const fragment = split[1];

        if (fragment.startsWith("/definitions/")) {
            return { base: base, ref: fragment.substring(13) };
        }

        return { base: base, ref: null };
    }

    private buildUrl(base, ref) {
        if (base == null && ref == null) {
            return null;
        }
        if (ref == null) {
            return `${base ?? ""}`;
        }
        return `${base ?? ""}#/definitions/${ref ?? ""}`;
    }

    initialDataChanged(newValue, oldValue) {
        if (newValue !== undefined) {
            const ref = newValue?.$ref ?? null;
            const value = this.splitUrl(ref);
            this.base = value.base;
            this.ref = value.ref;
        }
    }

    schemaChanged(newValue: NormalizedApiSchema, oldValue) {
        const normalized = newValue.normalized;
        this.description = normalized.description ?? "";
        this.isNullable = normalized.type.has(null);
        this.updateValid();
    }

    contextChanged(newValue, oldValue) {
        this.updateRefChoices();

        if (newValue?.baseApiLink?.href !== oldValue?.baseApiLink?.href) {
            this.updateNamespaceApiLink(newValue);
        }
    }

    valueInChanged(newValue) {
        const ref = newValue?.$ref ?? null;
        const value = this.splitUrl(ref);
        this.base = value.base;
        this.ref = value.ref;
    }

    baseChanged(newValue, oldValue) {
        this.valueChanged(
            this.buildUrl(newValue, this.ref),
            this.buildUrl(oldValue, this.ref),
        );
        this.updateBaseRefChoices();
        this.updateBaseApiLink();
    }
    refChanged(newValue, oldValue) {
        this.valueChanged(
            this.buildUrl(this.base, newValue),
            this.buildUrl(this.base, oldValue),
        );
    }

    private updateNamespaceApiLink(context) {
        this.namespaceApiLink = null;
        if (context?.baseApiLink == null) {
            this.namespaceApiLink = null;
            return;
        }

        this.apiService.getByApiLink(context?.baseApiLink).then(response => {
            this.namespaceApiLink = response.links.find(link => {
                if (link.resourceType !== "ont-namespace") {
                    return false;
                }
                if (link.rel.some(rel => rel === "collection")) {
                    return false;
                }
                if (link.rel.some(rel => rel === "nav" || rel === "up")) {
                    return true;
                }
                return false;
            });
        });
    }

    private async updateBaseApiLink() {
        if (this.base == null) {
            this.baseApiLink = null;
            return;
        }
        if (this.base === this.baseApiLink?.href) {
            return;  // nothing to update
        }
        try {
            const response = await this.apiService.getByApiLink<ApiObject>({
                href: this.base,
                resourceType: "ont-type-version",
                rel: [],
            }, false);
            if (response?.data?.self?.resourceType === "ont-type-version") {
                this.baseApiLink = response?.data?.self ?? null;
            }
        } catch {
            // do not update
        }
    }

    private async updateBaseSchemaFromApiLink(base: ApiLink) {
        // TODO: update schema link from api link
        let baseTypeVersionLink: ApiLink | null = null;
        if (base.resourceType === "ont-type") {
            const baseType = await this.apiService.getByApiLink<ApiObject>(base, false);
            baseTypeVersionLink = baseType.links.find(l => l.resourceType === "ont-type-version" && l.rel.some(r => r === "latest"));
        }
        if (base.resourceType === "ont-type-version") {
            baseTypeVersionLink = base;
        }
        if (baseTypeVersionLink == null) {
            // TODO: present error to user
            console.warn("Did not find latest version of type ", base);
            return;
        }

        this.baseApiLink = baseTypeVersionLink;
        this.base = baseTypeVersionLink.href;
    }

    private async updateBaseRefChoices() {
        const choices: ReferenceChoice[] = [];
        if (this.base) {
            const baseSchema = await this.schemas.getSchema(this.base);
            baseSchema.getDefinedTypes().forEach(typeDef => {
                choices.push({
                    key: typeDef.key,
                    // eslint-disable-next-line no-ternary
                    title: typeDef.title ? `${typeDef.title} (${typeDef.key})` : typeDef.key,
                });
            });
        }
        this.baseTypeChoices = choices;
        this.updateRefChoices();
    }

    private updateRefChoices() {
        const choices: ReferenceChoice[] = [];
        if (!this.base) {
            // add ref targets from current type to choices
            choices.push(...(this.context?.topLevelTypeDefs ?? []));
        } else {
            // add ref targets from base schema to choices
            choices.push(...(this.baseTypeChoices));
        }

        // always include the current ref value if any
        if (this.ref && choices.every(c => c.key !== this.ref)) {
            choices.unshift({
                "key": this.ref,
                "title": this.ref,
            });
        }
        this.refChoices = choices;
    }

    valueChanged(newValue, oldValue) {
        this.valueOut = { $ref: newValue };
    }

    valueOutChanged(newValue) {
        if (this.initialData === undefined) {
            this.dirty = newValue != null;
        } else {
            this.dirty = this.initialData !== newValue;
        }
        this.updateValid();
    }

    updateValid() {
        if (this.schema == null) {
            this.valid = false;
            return;
        }
        this.queue.queueMicroTask(() => { // this prevents updates getting lost
            if (this.base == null && this.ref == null) {
                this.valid = this.isNullable;
                return;
            }
            // TODO better valid check
            this.valid = true;
        });
    }

    openRefBaseChooser() {
        if (this.namespaceApiLink == null) {
            return;
        }
        const model = {
            referenceType: new Set(["ont-type", "ont-type-version"]),
            baseApiLink: this.namespaceApiLink,
        };
        this.dialogService.open({ viewModel: ApiObjectChooserDialog, model: model, lock: false }).whenClosed(response => {
            if (!response.wasCancelled) {
                this.updateBaseSchemaFromApiLink(response.output as ApiLink);
            } else {
                // do nothing on cancel
            }
        });
    }

    unsetRefBase() {
        this.ref = null;
        this.base = null;
    }

}
