import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { GastosService } from '../../services/gastos.service';
import { Gasto } from '../../models/gasto.model';

@Component({
  selector: 'app-results-panel',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './results-panel.component.html',
  styleUrls: ['./results-panel.component.css']
})
export class ResultsPanelComponent implements OnInit {
  gastos: Gasto[] = [];
  powerBiUrl: SafeResourceUrl;
  showFullscreen = false;

  constructor(
    private gastosService: GastosService,
    private sanitizer: DomSanitizer
  ) {
    const powerBiEmbedUrl = 'https://app.powerbi.com/view?r=eyJrIjoiYjc4NDc2NGUtNmEzNS00MmU2LThlNzUtY2E2Yjc0M2UyYTg3IiwidCI6ImNiYzJjMzgxLTJmMmUtNGQ5My05MWQxLTUwNmM5MzE2YWNlNyIsImMiOjR9';
    this.powerBiUrl = this.sanitizer.bypassSecurityTrustResourceUrl(powerBiEmbedUrl);
  }

  ngOnInit(): void {
    this.gastosService.gastos$.subscribe(gastos => {
      this.gastos = gastos;
    });
  }

  openFullscreen(): void {
    this.showFullscreen = true;
    // Prevenir scroll del body
    document.body.style.overflow = 'hidden';
  }

  closeFullscreen(): void {
    this.showFullscreen = false;
    // Restaurar scroll del body
    document.body.style.overflow = 'auto';
  }
}