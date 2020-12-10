import { Directive, ElementRef, HostListener } from '@angular/core';

declare const annotator: any;

@Directive({
  selector: '[appAnnotator]'
})
export class AnnotatorDirective {

  private callerElement:ElementRef;
  private conceptId: string;
  private documentId: string;
  private annotationType: string;
  private app;

  constructor(el: ElementRef) {
    this.callerElement = el;
  }

  ngOnInit() {
    var self = this;
    this.conceptId = this.callerElement.nativeElement.getAttribute("concept-id");
    this.documentId = this.callerElement.nativeElement.getAttribute("doc-id");
    this.annotationType = this.callerElement.nativeElement.getAttribute("annotation-type");

    self.app = new annotator.App();
    self.app.include(annotator.ui.main, {
      element: this.callerElement.nativeElement
    });
    self.app.include(annotator.storage.http, {
      prefix: 'http://localhost:8000/glossary/api/annotations/' + this.annotationType + "/" + this.conceptId + "/" + this.documentId
    });
    self.app.start().then(function () {
      self.app.annotations.load();
    });
  }

  @HostListener('click', ['$event']) onClick($event){
    this.app.annotations.load();
}

}

