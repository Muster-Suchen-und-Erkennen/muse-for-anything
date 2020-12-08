export class EmptyBindingBehavior {
    bind(binding, source) {
        binding.targetObserver = new EmptyAttrObserver(binding.target, binding.targetProperty);
    }

    unbind(binding, source) {/* nothing to do */ }
}

class EmptyAttrObserver {

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
        if (newValue) {
            this.element.setAttribute(this.propertyName, "");
        } else {
            this.element.removeAttribute(this.propertyName);
        }
    }

    subscribe() {
        throw new Error(`Observation of a "${this.element.nodeName}" element\'s "${this.propertyName}" property is not supported.`);
    }
}

