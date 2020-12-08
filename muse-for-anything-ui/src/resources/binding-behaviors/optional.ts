export class OptionalBindingBehavior {
    bind(binding, source) {
        binding.targetObserver = new OptionalAttrObserver(binding.target, binding.targetProperty);
    }

    unbind(binding, source) {/* nothing to do */ }
}

class OptionalAttrObserver {

    private element: Element;
    private propertyName: string;

    constructor(element, propertyName) {
        this.element = element;
        this.propertyName = propertyName;
    }

    getValue() {
        return this.element.getAttribute(this.propertyName);
    }

    setValue(newValue) {
        if (newValue == null) {
            this.element.removeAttribute(this.propertyName);
        } else {
            this.element.setAttribute(this.propertyName, newValue);
        }
    }

    subscribe() {
        throw new Error(`Observation of a "${this.element.nodeName}" element\'s "${this.propertyName}" property is not supported.`);
    }
}
