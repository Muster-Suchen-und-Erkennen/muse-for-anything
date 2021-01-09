import { bindable, bindingMode, observable } from "aurelia-framework";
import { NormalizedApiSchema, PropertyDescription } from "rest/schema-objects";

export class ObjectForm {
    @bindable key: string;
    @bindable label: string;
    @bindable initialData: any;
    @bindable schema: NormalizedApiSchema;
    @bindable debug: boolean = false;
    @bindable valuePush: any;
    @bindable({ defaultBindingMode: bindingMode.twoWay }) value: any = {};
    @bindable({ defaultBindingMode: bindingMode.fromView }) valid: boolean;
    @bindable({ defaultBindingMode: bindingMode.fromView }) dirty: boolean;

    properties: PropertyDescription[] = [];
    propertiesByKey: Map<string, PropertyDescription> = new Map();
    required: Set<string> = new Set();

    updateCount = 100;

    @observable() propertiesValid = {};
    @observable() propertiesDirty = {};

    initialDataChanged(newValue, oldValue) {
        this.reloadProperties();
    }

    schemaChanged(newValue, oldValue) {
        this.valid = null;
        this.reloadProperties();
    }

    reloadProperties() {
        if (this.schema == null) {
            this.properties = [];
            this.required = new Set();
            return;
        }
        if (this.schema.normalized.type == null || !this.schema.normalized.type.has("object")) {
            console.error("Not an object!"); // FIXME better error!
            this.properties = [];
            this.required = new Set();
            return;
        }
        const currentData = { // TODO refactor to be less costly (maybe use set?)
            ...this.initialData,
            ...(this.value ?? {}),
        };
        const properties = this.schema.getPropertyList(Object.keys(currentData));
        const propertiesByKey = new Map<string, PropertyDescription>();
        properties.forEach(prop => propertiesByKey.set(prop.propertyName, prop));
        this.properties = properties;
        this.propertiesByKey = propertiesByKey;
        this.required = this.schema.normalized.required;
    }

    updateSignal() {
        this.propertiesValidChanged(this.propertiesValid);
        this.propertiesDirtyChanged(this.propertiesDirty);
    }

    valueChanged(newValue) {
        this.reloadProperties();
    }

    propertiesValidChanged(newValue: { [prop: string]: boolean }) {
        if (newValue == null) {
            this.valid = false;
            return;
        }
        const propKeys = Object.keys(this.value ?? {});
        const allPropertiesValid = propKeys.every(key => newValue[key]);
        const requiredPropKeys = propKeys.filter(key => this.required.has(key));
        const allRequiredPresent = this.required.size === requiredPropKeys.length;
        this.valid = allPropertiesValid && allRequiredPresent;
    }

    propertiesDirtyChanged(newValue: { [prop: string]: boolean }) {
        if (newValue == null) {
            this.dirty = false;
            return;
        }
        const propKeys = Object.keys(this.value ?? {});
        this.dirty = (propKeys.length === 0) || propKeys.some(key => newValue[key]);
    }
}
