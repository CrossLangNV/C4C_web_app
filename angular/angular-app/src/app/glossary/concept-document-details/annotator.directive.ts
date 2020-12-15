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

  private readonly annotationStoreAddress = 'http://localhost:8000/glossary/api/annotations/';
  private readonly conceptIdAttributeName = 'concept-id';
  private readonly documentIdAttributeName = 'doc-id';
  private readonly annotationTypeAttributeName = 'annotation-type';

  constructor(el: ElementRef) {
    this.callerElement = el;
  }

  ngOnInit() {
    var self = this;
    this.conceptId = this.callerElement.nativeElement.getAttribute(this.conceptIdAttributeName);
    this.documentId = this.callerElement.nativeElement.getAttribute(this.documentIdAttributeName);
    this.annotationType = this.callerElement.nativeElement.getAttribute(this.annotationTypeAttributeName);

    self.app = new annotator.App();
    self.app.include(annotator.ui.main, {
      element: this.callerElement.nativeElement
    });
    self.app.include(annotator.storage.http, {
      prefix: this.annotationStoreAddress + this.annotationType + "/" + this.conceptId + "/" + this.documentId
    });
    self.app.start().then(function () {
      self.app.annotations.load();
    });
  }

  @HostListener('click', ['$event']) onClick($event){
    this.app.annotations.load();
}

}

