import { bindable } from "aurelia-framework";
import { ListNodeModel } from "./ontology-graph";
 
export class TreeNode {
  @bindable current: ListNodeModel;
}
