import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})
export class SidebarComponent {
  @Output() sectionChange = new EventEmitter<string>();
  activeSection = 'chat';

  selectSection(section: string): void {
    this.activeSection = section;
    this.sectionChange.emit(section);
  }
}