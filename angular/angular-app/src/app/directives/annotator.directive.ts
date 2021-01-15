import { Directive, ElementRef, HostListener } from '@angular/core';
import { Environment } from '../../environments/environment-variables';

declare const annotator: any;

@Directive({
  selector: '[appAnnotator]'
})
export class AnnotatorDirective {

  private callerElement:ElementRef;
  private subjectId: string;
  private documentId: string;
  private annotationType: string;
  private app;

  private readonly ANNOTATION_STORE_ADDRESS_GLOSSARY = Environment.ANGULAR_DJANGO_API_GLOSSARY_ANNOTATIONS_URL;
  private readonly ANNOTATION_STORE_ADDRESS_RO = Environment.ANGULAR_DJANGO_API_RO_ANNOTATIONS_URL;
  private readonly subjectIdAttributeName = 'subject-id';
  private readonly documentIdAttributeName = 'doc-id';
  private readonly annotationTypeAttributeName = 'annotation-type';

  constructor(el: ElementRef) {
    this.callerElement = el;
  }

  ngOnInit() {
    var self = this;
    this.subjectId = this.callerElement.nativeElement.getAttribute(this.subjectIdAttributeName);
    this.documentId = this.callerElement.nativeElement.getAttribute(this.documentIdAttributeName);
    this.annotationType = this.callerElement.nativeElement.getAttribute(this.annotationTypeAttributeName);

    var annotationStoreAddress = this.ANNOTATION_STORE_ADDRESS_GLOSSARY;
    if (this.annotationType == "ro") {
      annotationStoreAddress = this.ANNOTATION_STORE_ADDRESS_RO;
    }

    self.app = new annotator.App();
    self.app.include(annotator.ui.main, {
      element: this.callerElement.nativeElement
    });
    self.app.include(annotator.storage.http, {
      prefix: annotationStoreAddress + "/" + this.annotationType + "/" + this.subjectId + "/" + this.documentId
    });
    self.app.start().then(function () {
      self.app.annotations.load();
    });
  }

  @HostListener('click', ['$event']) onClick($event){
    this.app.annotations.load();
}

}

