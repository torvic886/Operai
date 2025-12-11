import { Component, OnInit } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-powerbi-panel',
  standalone: true,
  imports: [CommonModule],  
  templateUrl: './powerbi-panel.component.html',
  styleUrls: ['./powerbi-panel.component.css']
})
export class PowerbiPanelComponent implements OnInit {

  powerBiUrl!: SafeResourceUrl;
  showFullscreen = false;

  private readonly powerBiEmbedUrl =
    'https://app.powerbi.com/reportEmbed?reportId=72b391cf-91e7-4695-bd70-094494ff04aa&autoAuth=true&ctid=d3eb04d5-5d9f-4e83-ae9e-51d614d1e8cf';

  constructor(private sanitizer: DomSanitizer) {}

  ngOnInit(): void {
    // 🔥 Convertimos la URL en un recurso seguro para Angular
    this.powerBiUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
      this.powerBiEmbedUrl
    );
  }

  openFullscreen() {
    this.showFullscreen = true;
  }

  closeFullscreen() {
    this.showFullscreen = false;
  }
}
